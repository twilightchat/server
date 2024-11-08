import asyncio
import asyncpg
from quart import Quart, jsonify, request, websocket
from quart_cors import cors
import json
import random
import hmac
from datetime import datetime
from hypercorn.asyncio import serve
from hypercorn.config import Config
from twilightchat.enums import *
from twilightchat.types import *
from twilightchat.token import Token
import json
import zlib
from typing import Any

app = Quart(__name__)
app = cors(app)

# Database configuration
POSTGRES = {
    "host": "localhost",
    "user": "postgres",
    "password": "AMP@amp1024",
    "database": "twilightchat",
    "port": "5432"
}

db_pool = None  # Initialize the database connection pool

# Constants for Discord-like op codes and events
# Define the OPCODES dictionary according to the provided mapping
OPCODES = {
    'Dispatch': 0,
    'Heartbeat': 1,
    'Identify': 2,
    'Presence Update': 3,
    'Voice State Update': 4,
    'Resume': 6,
    'Reconnect': 7,
    'Request Guild Members': 8,
    'Invalid Session': 9,
    'Hello': 10,
    'Heartbeat ACK': 11,
}

CLOSE_CODES = {
    "Unknown error": 4000,
    "Unknown opcode": 4001,
    "Decode error": 4002,
    "Not authenticated": 4003,
    "Authentication failed": 4004,
    "Already authenticated": 4005,
    "Invalid seq": 4007,
    "Rate limited": 4008,
    "Session timed out": 4009,
    "Invalid shard": 4010,
    "Sharding required": 4011,
    "Invalid API version": 4012,
    "Invalid intent(s)": 4013,
    "Disallowed intent(s)": 4014,
}

# In-memory storage for connected users and messages
connected_clients = {}

print("TwilightChat Server")
print(" * Starting server...")

# Custom error handler for 415 Unsupported Media Type
@app.errorhandler(415)
async def unsupported_media_type(error):
    return jsonify({
        "error": "Unsupported Media Type",
        "message": "The server cannot process the request payload because the media type is unsupported."
    }), 415

# Token secret
TOKEN_SECRET = "35c8b2f70a8b01c2a2fe3d3f8e8b9977"

# Heartbeat interval constant
HEARTBEAT_INTERVAL_DEFAULT = random.randint(40, 46) * 1000  # Default heartbeat interval


# Custom error handler for 415 Unsupported Media Type
@app.errorhandler(415)
async def unsupported_media_type(error):
    return jsonify({
        "error": "Unsupported Media Type",
        "message": "The server cannot process the request payload because the media type is unsupported."
    }), 415

# Token secret
TOKEN_SECRET = "35c8b2f70a8b01c2a2fe3d3f8e8b9977"

# Heartbeat interval constant
HEARTBEAT_INTERVAL_DEFAULT = random.randint(40, 46) * 1000  # Default heartbeat interval

def gen_session_id():
    """Generate a random session ID."""
    return f"{Snowflake.generate(random.randint(0, 31), random.randint(0, 31))}"

async def heartbeat(websocket):
    """Sends a heartbeat to the client."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_DEFAULT / 1000)  # Convert ms to seconds
        if websocket in connected_clients:
            await send_as_array_buffer(websocket, {'op': OPCODES['Heartbeat'], 'd': {}})

def want_bytes(data):
    """Helper function to ensure data is in bytes."""
    if isinstance(data, str):
        return data.encode('utf-8')
    return data

async def _zlib_stream_send(websocket, encoded):
    # Access the connected client's properties
    properties = connected_clients[websocket]  # Retrieve properties of the current websocket

    # Compress and flush (for the rest of compressed data + ZLIB_SUFFIX)
    data1 = properties['zctx'].compress(encoded)  # Use 'zctx' from properties
    data2 = properties['zctx'].flush(zlib.Z_FULL_FLUSH)
    data = data1 + data2

    print(
        "zlib-stream: length {} -> compressed ({})",
        len(encoded),
        len(data),
    )

    # Send data as bytes
    await websocket.send(data)  # This sends data as bytes, which is correct

async def send_as_array_buffer(websocket, payload):
    """Send payload with conditional compression."""
    # Convert the payload to JSON and encode it to bytes
    encoded = json.dumps(payload).encode('utf-8')

    # Access the connected client's properties
    properties = connected_clients[websocket]

    # Check the compression settings and send accordingly
    await _zlib_stream_send(websocket, want_bytes(encoded))

@app.websocket('/')
async def handle_websocket():
    """Handle WebSocket connections."""
    session_id = gen_session_id()
    
    # Initialize connection properties
    connected_clients[websocket] = {
        'session_id': session_id,
        'sequence': 0,
        'heartbeat_interval': HEARTBEAT_INTERVAL_DEFAULT,
        'authenticated': True,
        'compress': 'zlib-stream',  # or 'zstd-stream' depending on your requirements
        'encoding': 'json',  # or 'etf' as per your logic
        'zctx': zlib.compressobj()  # Initialize zlib compression context
    }

    # Send Hello message to the client
    hello_payload = {
        'op': OPCODES['Hello'],
        'd': {"heartbeat_interval": HEARTBEAT_INTERVAL_DEFAULT, "_trace": ["twilightchat-gateway-server"]}
    }
    await send_as_array_buffer(websocket, hello_payload)

    # Start heartbeat task
    asyncio.create_task(heartbeat(websocket))

    try:
        while True:
            message = await websocket.receive()
            await handle_message(message, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in connected_clients:
            del connected_clients[websocket]
            print(f'Client {websocket} disconnected')

async def handle_message(message, websocket):
    """Handle incoming WebSocket messages."""
    # Check if the message is bytes or str and handle accordingly
    if isinstance(message, bytes):
        data = json.loads(message.decode('utf-8'))  # Decode from bytes to string
    elif isinstance(message, str):
        data = json.loads(message)  # If it's already a string, just parse JSON
    else:
        print("Received unknown message type:", type(message))
        return  # You can also choose to close the websocket here if you prefer

    op = data.get('op')
    if op == OPCODES['Identify']:
        await handle_identify(data, websocket)
    elif op == OPCODES['Heartbeat']:
        await handle_heartbeat(data, websocket)
    elif op == OPCODES['Status Update']:
        await handle_status_update(data, websocket)
    elif op == OPCODES['Voice Update']:
        await handle_voice_update(data, websocket)
    elif op == OPCODES['Voice Ping']:
        await handle_voice_ping(data, websocket)
    elif op == OPCODES['Resume']:
        await handle_resume(data, websocket)
    elif op == OPCODES['Reconnect']:
        await handle_reconnect(data, websocket)
    elif op == OPCODES['Request Guild Members']:
        await handle_request_guild_members(data, websocket)
    elif op == OPCODES['Guild Sync']:
        await handle_guild_sync(data, websocket)
    elif op == OPCODES['Call Sync']:
        await handle_call_sync(data, websocket)
    elif op == OPCODES['Lazy Request']:
        await handle_lazy_request(data, websocket)
    else:
        print(f"Received unknown operation: {op}")
        await websocket.close(1003)  # Unsupported Data

async def handle_heartbeat(data, websocket):
    """Handle heartbeat messages from clients."""
    # Log the heartbeat receipt for debugging purposes
    print("Received ", data)

    # Respond to the heartbeat to acknowledge receipt
    response = {
        'op': OPCODES['Heartbeat ACK'],  # Use the appropriate opcode for acknowledgment
        'd': None,  # Heartbeat ACK doesn't need additional data
        's': None,
        't': None
    }

    await send_as_array_buffer(websocket, response)  # Send acknowledgment back to the client
    
    print("Sent ", response)
    
async def handle_identify(data, websocket):
    """Handle identify requests from clients."""
    
    if websocket not in connected_clients:
        await websocket.close(CLOSE_CODES['Not authenticated'])
        return

    token = data.get('d', {}).get('token')  # Safely get the token

    if not token:
        await send_as_array_buffer(websocket, {
            'code': CLOSE_CODES['Not authenticated'],
            'message': 'Token is required.'
        })
        await websocket.close(CLOSE_CODES['Not authenticated'])
        return

    try:
        async with db_pool.acquire() as connection:
            user = await connection.fetchrow('SELECT * FROM users WHERE token = $1', token)

            if user:
                connected_clients[websocket]['authenticated'] = True
                connected_clients[websocket]['user'] = user

                # Prepare the response payload directly as OP JSON
                response_payload = {
                    'op': OPCODES['Dispatch'],  # Use the dispatch opcode
                    'd': {
                        'user': {
                            'id': user['id'],
                            'username': user['username'],
                            'discriminator': user['discriminator'],
                            'avatar': user['avatar'],
                            'flags': user['flags'],
                            'verified': user['verified'],
                        },
                    }
                }
                await send_as_array_buffer(websocket, response_payload)  # Correctly send as bytes
            else:
                await send_as_array_buffer(websocket, {
                    'code': CLOSE_CODES['Authentication failed'],
                    'message': 'Authentication failed or user not found.'
                })
                await websocket.close(CLOSE_CODES['Authentication failed'])
    except Exception as e:
        print(f"Error during identify: {e}")

async def handle_status_update(data, websocket):
    """Handle status update requests from clients."""
    if websocket not in connected_clients:
        await websocket.close(CLOSE_CODES['Not authenticated'])
        return

    # Example structure of status update
    status = data.get('d', {}).get('status')
    print(f"Status update from {connected_clients[websocket]['user']['username']}: {status}")

    # Respond back if needed, e.g., broadcast to other clients
    # You could implement more complex presence logic here

async def handle_voice_update(data, websocket):
    """Handle voice state updates from clients."""
    if websocket not in connected_clients:
        await websocket.close(CLOSE_CODES['Not authenticated'])
        return

    # Example structure for voice update
    print(f"Voice update from {connected_clients[websocket]['user']['username']}: {data.get('d')}")

async def handle_voice_ping(data, websocket):
    """Handle voice ping messages."""
    if websocket not in connected_clients:
        await websocket.close(CLOSE_CODES['Not authenticated'])
        return

    print(f"Voice ping from {connected_clients[websocket]['user']['username']}")

async def handle_resume(data, websocket):
    """Handle resume requests from clients."""
    # Resuming logic can be implemented here
    print(f"Resume request from {connected_clients[websocket]['user']['username']}")

async def handle_reconnect(data, websocket):
    """Handle reconnect requests from clients."""
    # Reconnect logic can be implemented here
    print(f"Reconnect request from {connected_clients[websocket]['user']['username']}")

async def handle_guild_sync(data, websocket):
    """Handle guild sync requests from clients."""
    # Guild sync logic can be implemented here
    print(f"Guild sync request from {connected_clients[websocket]['user']['username']}")

async def handle_call_sync(data, websocket):
    """Handle call sync requests."""
    # Call sync logic can be implemented here
    print(f"Call sync request from {connected_clients[websocket]['user']['username']}")

async def handle_lazy_request(data, websocket):
    """Handle lazy requests."""
    # Lazy request logic can be implemented here
    print(f"Lazy request from {connected_clients[websocket]['user']['username']}")

def validate_token(token: str, user: dict, token_secret: str) -> bool:
    """Validate the token against the user's credentials and token secret."""
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        part_one = parts[0] + '.' + parts[1]  # Combine part 1 and part 2
        received_hmac = parts[2]  # Get the HMAC

        # Generate the expected HMAC
        key = f"{token_secret}--{user['password']}"
        expected_hmac = generate_hmac(key, part_one)
        encoded_expected_hmac = encode_hmac(expected_hmac)

        # Compare the received HMAC with the expected HMAC
        return hmac.compare_digest(received_hmac, encoded_expected_hmac)
    except Exception as e:
        print(f"Error during token validation: {e}")
        return False

# Database connection initialization
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=POSTGRES["host"],
        user=POSTGRES["user"],
        password=POSTGRES["password"],
        database=POSTGRES["database"],
        port=POSTGRES["port"]
    )

@app.route('/api/v8/auth/register', methods=['POST'])
async def register_user():
    data = await request.json

    # Check for required fields
    if not data or 'email' not in data or 'username' not in data or 'password' not in data:
        return jsonify({"code": 50005, "message": "Email, username and password are required."}), 400

    email = data['email']
    username = data['username']
    password = data['password']
    
    discriminator = Discriminator.generate()

    # Acquire a connection from the pool manually
    con = await db_pool.acquire()  # Get a connection from the pool
    try:
        # Check if the username already exists
        existing_user = await con.fetchrow('SELECT * FROM users WHERE email = $1', username)
        if existing_user:
            return jsonify({"code": 10013, "message": "Username already exists"}), 409  # Conflict: User already exists
    finally:
        await con.close()
        
    con = await db_pool.acquire()  # Get a connection from the pool
    try:
        # Generate a unique user ID and hash the password
        user_id = Snowflake.generate(random.randint(0, 31), random.randint(0, 31))

        # Prepare the User object
        user = User(
            id=user_id,
            username=username,
            discriminator=discriminator,
            password=password,  # Store the hashed password
            email=email
        )
        user.token = Token(user, TOKEN_SECRET).token  # Generate a token

        # Insert the new user into the database
        await con.execute('''
            INSERT INTO users (id, username, password_hash, discriminator, avatar, banner, accent_color, bot, email, token, locale, mfa_enabled, premium_type, public_flags, flags, verified, system)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
        ''', user.id, user.username, user.password.decode('utf-8'), user.discriminator, user.avatar, user.banner, user.accent_color,
        user.bot, user.email, user.token, user.locale, user.mfa_enabled, user.premium_type, user.public_flags,
        user.flags, user.verified, user.system)

        return jsonify(user.to_dict()), 201  # Created

    except Exception as e:
        print(f"Error during user registration: {e}")
        return jsonify({"code": 500, "message": "Internal Server Error"}), 500  # Internal Server Error

    finally:
        await db_pool.release(con)  # Release the connection back to the pool

@app.route('/api/v8/auth/login', methods=['POST'])
async def login_user():
    data = await request.json

    # Check for required fields
    if not data or 'login' not in data or 'password' not in data:
        return jsonify({"code": 50005, "message": "Username and password are required."}), 400

    username = data['login']
    password = data['password']

    # Acquire a connection from the pool
    con = await db_pool.acquire()
    try:
        # Fetch the user from the database
        user_row = await con.fetchrow('SELECT * FROM users WHERE email = $1', username)
        
        # Check if the user exists
        if user_row is None:
            return jsonify({"code": 10013, "message": "Invalid username or password."}), 401  # Unauthorized

        # Verify the password
        hashed_password = user_row['password_hash']  # Adjust based on your database schema
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return jsonify({"code": 10013, "message": "Invalid username or password."}), 401  # Unauthorized

        # Create the user object from the fetched data
        user = {
            'id': user_row['id'],
            'username': user_row['username'],
            'discriminator': user_row['discriminator'],
            'avatar': user_row['avatar'],  # Include other fields if necessary
            'token': user_row['token']  # Generate a token
        }

        return jsonify(user), 200  # Success

    except Exception as e:
        print(f"Error during user login: {e}")
        return jsonify({"code": 500, "message": "Internal Server Error"}), 500  # Internal Server Error

    finally:
        await db_pool.release(con)  # Release the connection back to the pool

# Message Handling Endpoint
@app.route('/api/v8/channels/<channel_id>/messages', methods=['POST'])
async def send_message(channel_id):
    data = await request.json
    content = data.get('content')
    author = data.get('author')  # Assuming you provide the author ID in the request
    mentions = data.get('mentions', [])
    embeds = data.get('embeds', [])
    attachments = data.get('attachments', [])
    stickers = data.get('stickers', [])
    tts = data.get('tts', False)
    pinned = data.get('pinned', False)
    mention_everyone = data.get('mention_everyone', False)

    if not content:
        return jsonify({"code": 50005, "message": "Cannot send an empty message"}), 400  # Cannot send an empty message

    # Generate a unique message ID
    message_id = Snowflake.generate(random.randint(0, 31), random.randint(0, 31))

    # Create the Message instance
    message = Message(
        id=message_id,
        channel_id=channel_id,
        author=author,
        content=content,
        mentions=mentions,
        embeds=embeds,
        attachments=attachments,
        stickers=stickers,
        tts=tts,
        pinned=pinned,
        mention_everyone=mention_everyone
    )

    async with db_pool.acquire() as connection:
        await connection.execute('''
            INSERT INTO messages (id, channel_id, author, content, timestamp, tts, pinned, mention_everyone, 
                                  mentions, embeds, attachments, stickers) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 
                                  $9, $10, $11, $12)
        ''', message.id, message.channel_id, message.author, message.content, datetime.utcnow(), message.tts, message.pinned, 
        message.mention_everyone, json.dumps(message.mentions), json.dumps(message.embeds), json.dumps(message.attachments), json.dumps(message.stickers))

    return jsonify(message.to_dict()), 201  # Created

# Message Handling Endpoint
@app.route('/api/v8/gateway', methods=['GET'])
async def get_gateway():
    return jsonify({"url": "ws://localhost:5000"}), 201  # Created

async def main():
    await init_db()  # Initialize the database
    # Hypercorn configuration
    config = Config()
    config.bind = ["127.0.0.1:5000"]
    # Start the server
    await serve(app, config)

# Run the Quart app
if __name__ == "__main__":
    asyncio.run(main())
