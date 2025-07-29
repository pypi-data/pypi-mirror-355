import os
import re


class HandlerService:
    def __init__(self, name: str, subscribe: str = None, publish: str = None):
        self.name = name
        self.subscribe = subscribe
        self.publish = publish
        self.home_directory = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        self.current_directory = os.getcwd()
        self.destination_folder = "handlers"
        self.file_name = re.sub(r"\d", "", f"{self.name}.py").lower()
        self.file_path = os.path.join(
            self.current_directory, self.destination_folder, self.file_name
        )

        self.stub_folder = os.path.join(self.home_directory, "stubs", "handler")
        self.source_stub = self.determine_source_stub()

    def determine_source_stub(self):
        if self.subscribe and self.publish:
            return os.path.join(self.stub_folder, "sqs_both.stub")
        elif self.subscribe:
            return (
                os.path.join(self.stub_folder, "sqs_subscribe.stub")
                if self.subscribe == "sqs"
                else os.path.join(self.stub_folder, "sns.stub")
            )
        elif self.publish:
            return os.path.join(self.stub_folder, "sqs_publish.stub")
        else:
            print("No specific option chosen.")
            return os.path.join(self.stub_folder, "default.stub")

    def create_handler_file(self):
        try:
            if not os.path.exists(
                os.path.join(self.current_directory, self.destination_folder)
            ):
                os.makedirs(
                    os.path.join(
                        self.current_directory, self.destination_folder
                    )
                )
                print(f"Created '{self.destination_folder}' folder.")

            if os.path.exists(self.file_path):
                with open(self.file_path, "r") as dest_file:
                    dest_content = dest_file.read()

                    if "{{ sqs_listen }}" in dest_content and self.subscribe:
                        print(
                            "Destination already has SQS subscription placeholder. Consider updating manually."
                        )
                        return

                    if "{{ sqs_publish }}" in dest_content and self.publish:
                        print(
                            "Destination already has SQS publishing placeholder. Consider updating manually."
                        )
                        return

            with open(self.source_stub, "r") as source_file:
                handler_stub_content = source_file.read()

            # Insert subscribe and publish code if necessary
            handler_stub_content = self.insert_subscribe_publish_code(
                handler_stub_content
            )

            with open(self.file_path, "w") as destination_file:
                destination_file.write(handler_stub_content)

            print(f"File '{self.file_path}' updated successfully.")

        except FileNotFoundError:
            print(f"File '{self.source_stub}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def insert_subscribe_publish_code(self, handler_stub_content):
        if self.subscribe or (self.subscribe and self.publish):
            handler_stub_content = self.insert_code_block(
                handler_stub_content, "sqs_listen.stub", "{{ sqs_listen }}"
            )

        if self.publish or (self.subscribe and self.publish):
            handler_stub_content = self.insert_code_block(
                handler_stub_content, "sqs_trigger.stub", "{{ sqs_trigger }}"
            )

        return handler_stub_content

    def insert_code_block(self, content, stub_name, placeholder):
        # Construct the pattern string separately to avoid backslash in f-string curly braces
        pattern = r"^( *)" + re.escape(placeholder)
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            indentation = match.group(1)
            with open(
                os.path.join(self.stub_folder, stub_name), "r"
            ) as insert_file:
                code_to_insert = insert_file.read()
            indented_code_to_insert = code_to_insert.replace(
                "\n", "\n" + indentation
            )
            content = content.replace(placeholder, indented_code_to_insert, 1)
        return content

    def delete_handler_file(self):
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                print(f'File "{self.file_path}" deleted successfully.')
            except Exception as e:
                print(f"An error occurred while trying to delete the file: {e}")
        else:
            print(
                f'File "{self.file_path}" does not exist. No deletion needed.'
            )
