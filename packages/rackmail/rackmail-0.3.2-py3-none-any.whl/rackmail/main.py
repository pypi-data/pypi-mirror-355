import argparse
from .version import VERSION
from .subcommands.enable_user import enable_user
from .subcommands.disable_user import disable_user
from .subcommands.get_mailbox import get_mailbox
from .subcommands.set_property import set_property
from .subcommands.set_password import set_password

def main():
    main_parser = argparse.ArgumentParser(prog="rackmail",description="CLI to interact with Rackspace's Hosted Email API",)
    main_parser.add_argument("--version",action="version",version=f"{main_parser.prog} V.{VERSION}")

    # This is store two arguments, we can add this as a parent to sub parsers so they will use the --email and --domain arguments.
    global_command_parser = argparse.ArgumentParser(add_help=False)
    global_command_parser.add_argument("-e","--email",action="store",metavar="email",dest="email",help="the email address of a mailbox",required=True)
    global_command_parser.add_argument("-d","--domain",action="store",metavar="domain",dest="domain",help="the domain of a mailbox",required=True)

    subparsers = main_parser.add_subparsers(dest="command")

    enable_user_subcommand = subparsers.add_parser("enableuser",description="Enables a hosted mailbox",parents=[global_command_parser])
    enable_user_subcommand.set_defaults(func=enable_user)

    disable_user_subcommand = subparsers.add_parser("disableuser",description="Disables a hosted mailbox",parents=[global_command_parser])
    disable_user_subcommand.set_defaults(func=disable_user)
    get_mailbox_subcommand = subparsers.add_parser("getmailbox",description="Gets all available information about a mailbox",parents=[global_command_parser])
    get_mailbox_subcommand.set_defaults(func=get_mailbox)

    change_password_subcommand = subparsers.add_parser("setpassword",description="Sets the password of a mailbox",parents=[global_command_parser])
    change_password_subcommand.add_argument("-p","--password",action="store",metavar="password",dest="password",help="The password you want set on a mailbox",required=False,default=None)
    change_password_subcommand.set_defaults(func=set_password)

    set_subcommand = subparsers.add_parser(
        "set",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Set Rackspace API properties that don’t need their own command.\n"
            "Use this for things like BusinessUnit, TimeZone, or other one-off fields.\n\n"
            "Examples:\n"
            "  rackmail set BusinessUnit WaffleOps -e user.name -d mydomain.com\n"
            "  rackmail set TimeZone America/New_York -e user.name -d mydomain.com\n"
        ),
        epilog=(
            "For a list of all possible properties visit RackSpace Hosted Email API Reference\n"
            "http://api-wiki.apps.rackspace.com/api-wiki/index.php/Rackspace_Mailbox_(Rest_API)\n\n"
            "Note: This command does not validate property names or values—use it when you know what you’re doing."
        ),
        parents=[global_command_parser])
    set_subcommand.add_argument("property",action="store",metavar="property",help="The property being changed")
    set_subcommand.add_argument("value",action="store",metavar="value",help="The updated value of the property being changed")
    set_subcommand.set_defaults(func=set_property)
    
    args = main_parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        main_parser.print_help()

if __name__ == "__main__":
    main()