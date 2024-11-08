from twilightchat.enums import *
from twilightchat.types import *
from twilightchat.token import Token

def main():
    print("TwilightChat server infrastructure test")
    print("NOTE: No database yet, it is early stage development")
    username = password = "test"
    token_secret = "35c8..."

    datacenter_id = random.randint(0, 31)
    worker_id = random.randint(0, 31)
    user_id = str(Snowflake.generate(datacenter_id, worker_id))
    discriminator = Discriminator.generate()

    user = User(user_id, username, discriminator, password=password, premium_type=UserPremiumType.Nitro, flags=409857)
    token = Token(user, token_secret).token
    user.token = token
    
    has_nitro = user.premium_type > 0 and user.premium_type <= UserPremiumType.Nitro

    if has_nitro:
        nitro_type = "Nitro" if user.premium_type == UserPremiumType.Nitro else "Nitro Classic"
        
    print(f"User created! ID: {user_id}, Token: {token}, Has Nitro: {has_nitro}{', Nitro type: ' + nitro_type if has_nitro else ''}")
    print(f"User flags:")
    user_flags = user.flags
    for i in UserFlags.get_flag_names(user.flags):
        print(i)

    while True:
        flags_input = input("user flag (type 'quit' to exit): ")
        if flags_input.startswith("-"):
            flag_name = flags_input[1:]  # Remove the '-' prefix
            flag_value = getattr(UserFlags, flag_name.upper(), None)  # Get the flag value

            if flag_value is not None:
                # Toggle the flag
                user_flags &= ~flag_value
                print(f"Disabled {flag_name}. Current flags: {user_flags}")
                # Get and print active flag names
                active_flags = UserFlags.get_flag_names(user_flags)
                print("Active flags:", ", ".join(active_flags) if active_flags else "None")
            else:
                print(f"Invalid flag: {flag_name}")
        elif flags_input.startswith("+"):
            flag_name = flags_input[1:]  # Remove the '-' prefix
            flag_value = getattr(UserFlags, flag_name.upper(), None)  # Get the flag value

            if flag_value is not None:
                # Toggle the flag
                user_flags |= flag_value
                print(f"Enabled {flag_name}. Current flags: {user_flags}")
                # Get and print active flag names
                active_flags = UserFlags.get_flag_names(user_flags)
                print("Active flags:", ", ".join(active_flags) if active_flags else "None")
            else:
                print(f"Invalid flag: {flag_name}")
        elif flags_input == "quit":
            break
        else:
            print("Please enter a valid flag or 'quit' to exit.")
        
    adminRole = Role(
        id=Snowflake.generate(datacenter_id, worker_id),
        name="Administrator",
        permissions="8",
        position=1,
        color=0,
        hoist=False,
        managed=False,
        mentionable=False,
        tags=RoleTags('', '')
    )

    guild = Guild(
        id=Snowflake.generate(datacenter_id, worker_id),
        name="Shant",
        owner_id=user_id,
        application_id=user_id if user.bot else '',
        roles=[adminRole.to_dict()]
    )

    if not guild.name == "":
        print("Guild created with the following details:")
        print(guild.to_dict())
        everyoneRole = guild.roles[0]
        print(guild.roles)
        

if __name__ == "__main__":
    main()

