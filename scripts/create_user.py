import argparse

from models.user import UserModel


def create_user(mail, pwd, n):
    return UserModel.create_user(mail, pwd, n, None, None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add user script")

    parser.add_argument("-e", "--email", type=str, required=True, help="User email")
    parser.add_argument("-p", "--pwd", type=str, required=True, help="User password")
    parser.add_argument("-n", "--name", type=str, required=True, help="User name")

    args = parser.parse_args()

    email = args.email
    password = args.pwd
    first_name = args.name

    user, access_token = create_user(email, password, first_name)
    if user:
        print(user.first_name, user.email, user.first_name)
