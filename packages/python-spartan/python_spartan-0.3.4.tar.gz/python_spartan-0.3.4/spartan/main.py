import os
import shutil
import subprocess
import sys
from typing import Optional

import boto3
import botocore
import questionary
import typer
from alembic.config import Config

from spartan.services.application import ApplicationService
from spartan.services.debug import DebugService
from spartan.services.deployment import DeploymentService
from spartan.services.handler import HandlerService
from spartan.services.infrastructure import InfrastructureService
from spartan.services.migrate import MigrateService
from spartan.services.model import ModelService
from spartan.services.motivate import MotivateService
from spartan.services.request import RequestService
from spartan.services.response import ResponseService
from spartan.services.route import RouteService
from spartan.services.service import ServiceService

TEMPLATE_OPTIONS = [
    "Headless Starter Kit",
    "RESTful API Starter Kit",
    "Quit",
]

DEBUG_OPTIONS = [
    "Python File",
    "Python File with Arguments",
    "Module",
    "FastAPI",
    "Quit",
]


alembic_cfg = Config("alembic.ini")
app = typer.Typer()


def register_commands():
    model_app = typer.Typer()
    app.add_typer(
        model_app,
        name="model",
        help="Manages the creation and deletion of model classes.",
    )

    handler_app = typer.Typer()
    app.add_typer(
        handler_app,
        name="handler",
        help="Manages the creation and deletion of lambda files in the application.",
    )

    migrate_app = typer.Typer()
    app.add_typer(
        migrate_app,
        name="migrate",
        help="Manages database changes, like updates, rollbacks, and making new tables.",
    )

    request_app = typer.Typer()
    app.add_typer(
        request_app,
        name="request",
        help=" Manages the creation and deletion of request classes.",
    )

    service_app = typer.Typer()
    app.add_typer(
        service_app,
        name="service",
        help=" Manages the creation and deletion of service classes.",
    )

    route_app = typer.Typer()
    app.add_typer(
        route_app,
        name="route",
        help=" Manages the creation and deletion of route classes.",
    )

    response_app = typer.Typer()
    app.add_typer(
        response_app,
        name="response",
        help=" Manages the creation and deletion of response classes.",
    )

    db_app = typer.Typer()
    app.add_typer(db_app, name="db", help="Prepare your database tables.")

    infra_app = typer.Typer()
    app.add_typer(
        infra_app,
        name="infra",
        help="Setup your serverless infrastructure as a code.",
    )

    env_app = typer.Typer()
    app.add_typer(
        env_app,
        name="env",
        help="Setup your serverless environment variables.",
    )

    ecs_app = typer.Typer(no_args_is_help=True)
    app.add_typer(ecs_app, name="ecs", help="Manage ECS resources.")

    # bucket_app = typer.Typer(
    #     help="Manage S3 bucket operations (cp, mv, rename, sync) via AWS Glue jobs."
    # )
    # app.add_typer(
    #     bucket_app, name="bucket", help="Manage S3 bucket operations."
    # )

    debug_app = typer.Typer()
    app.add_typer(
        debug_app, name="debug", help="Generate VS Code launch configurations."
    )

    @model_app.command("create")
    def model_create(name: str):
        try:
            service = ModelService(name)
            service.create_model_file()
        except Exception as e:
            print(f"Error creating model: {e}")

    @model_app.command("delete", help="Delete an existing model class.")
    def model_delete(name: str):
        try:
            service = ModelService(name)
            service.delete_model_file()
        except Exception as e:
            print(f"Error deleting model: {e}")

    @service_app.command("create", help="Create a service class.")
    def service_create(name: str):
        try:
            service = ServiceService(name)
            service.create_service_file()
        except Exception as e:
            print(f"Error creating service: {e}")

    @route_app.command("create", help="Create a route class.")
    def route_create(name: str):
        try:
            route = RouteService(name)
            route.create_route_file()
        except Exception as e:
            print(f"Error creating route: {e}")

    @service_app.command("delete", help="Delete an existing service class.")
    def service_delete(name: str):
        try:
            service = ServiceService(name)
            service.delete_service_file()
        except Exception as e:
            print(f"Error deleting service: {e}")

    @route_app.command("delete", help="Delete an existing route class.")
    def route_delete(name: str):
        try:
            route = RouteService(name)
            route.delete_route_file()
        except Exception as e:
            print(f"Error deleting route: {e}")

    @handler_app.command(
        "create",
        help="Create a new handler file with optional subscribe and publish options.",
    )
    def handler_create(
        name: str,
        subscribe: str = typer.Option(
            None, "--subscribe", "-s", help="Subscribe option."
        ),
        publish: str = typer.Option(
            None, "--publish", "-p", help="Publish option."
        ),
    ):
        try:
            handler_service = HandlerService(
                name, subscribe=subscribe, publish=publish
            )
            handler_service.create_handler_file()
        except Exception as e:
            print(f"Error creating handler: {e}")

    @handler_app.command("delete", help="Delete an existing handler file.")
    def handler_delete(name: str):
        try:
            handler_service = HandlerService(name)
            handler_service.delete_handler_file()
        except Exception as e:
            print(f"Error deleting handler: {e}")

    @migrate_app.command(
        "upgrade", help="Upgrade the database schema to the latest version."
    )
    def migrate_upgrade():
        try:
            migrate_service = MigrateService(alembic_cfg)
            migrate_service.migrate_upgrade()
        except Exception as e:
            print(f"Error upgrading database: {e}")

    @migrate_app.command(
        "create",
        help="Create a new database migration with an optional message.",
    )
    def migrate_create(
        message: str = typer.Option(
            "", "--comment", "-c", help="Message option."
        ),
    ):
        try:
            migrate_service = MigrateService(alembic_cfg)
            migrate_service.migrate_create(message=message)
        except Exception as e:
            print(f"Error creating database migration: {e}")

    @migrate_app.command(
        "downgrade", help="Downgrade the database schema to a previous version."
    )
    def migrate_downgrade():
        try:
            migrate_service = MigrateService(alembic_cfg)
            migrate_service.migrate_downgrade()
        except Exception as e:
            print(f"Error downgrading database: {e}")

    @migrate_app.command("refresh", help="Refresh the database migrations.")
    def migrate_refresh():
        try:
            migrate_service = MigrateService(alembic_cfg)
            migrate_service.migrate_refresh()
        except Exception as e:
            print(f"Error refreshing database migrations: {e}")

    @migrate_app.command(
        "init",
        help="Initialize database migration with a specified database type.",
    )
    def migrate_init(
        database: str = typer.Option(
            None,
            "--database",
            "-d",
            help="The database type (sqlite, mysql, or psql)..",
        )
    ):
        try:
            migrate_service = MigrateService(alembic_cfg)
            if database not in ["sqlite", "mysql", "psql"]:
                typer.echo(
                    "Invalid or no database type specified. Please choose from 'sqlite', 'mysql', or 'psql'."
                )
                raise typer.Exit()
            migrate_service.migrate_initialize(database)
            typer.echo(f"Migration initialized for database type: {database}")
        except Exception as e:
            print(f"Error initializing database migration: {e}")

    @db_app.command("seed", help="Seed the database with initial data.")
    def db_seed():
        try:
            print("Seeding the database")
            if sys.platform == "darwin":
                subprocess.run(
                    ["python3", "-m", "database.seeders.database_seeder"]
                )
            else:
                subprocess.run(
                    ["python", "-m", "database.seeders.database_seeder"]
                )
            print("Done")
        except Exception as e:
            print(f"Error seeding the database: {e}")

    @infra_app.command(
        "init", help="Copy a YAML file for infrastructure as code."
    )
    def deploy_config(
        source: Optional[str] = typer.Option(
            None, help="Source file path (absolute or relative)"
        )
    ):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if source is None:
            destination = os.path.join(os.getcwd(), "serverless.yml")
            if os.path.exists(destination):
                typer.echo(
                    "'serverless.yml' already exists in the current directory. Aborting."
                )
                raise typer.Abort()
            try:
                stub_file = os.path.join(
                    base_dir, "stubs", "infrastructure", "serverless.stub"
                )
                shutil.copy(stub_file, destination)
                typer.echo(
                    "File generated to the current working directory as 'serverless.yml'."
                )
            except Exception as e:
                typer.echo(f"Error copying file: {e}")
            return
        try:
            deployment_service = DeploymentService()
            deployment_service.config(source)
        except Exception as e:
            typer.echo(f"Error configuring deployment: {e}")

    @app.command(
        "motivate",
        help="Displays a random inspirational quote and its author for the Spartan like you.",
    )
    def inspire_display():
        try:
            inspiration_service = MotivateService()
            quote = inspiration_service.get_random_quote()
            typer.echo(quote)
        except Exception as e:
            print(f"Error displaying inspirational quote: {e}")

    @request_app.command("create", help="Create a new request class.")
    def request_create(name: str):
        try:
            service = RequestService(name)
            service.create_request_file()
        except Exception as e:
            print(f"Error creating request: {e}")

    @request_app.command("delete", help="Delete an existing request class.")
    def request_delete(name: str):
        try:
            service = RequestService(name)
            service.delete_request_file()
        except Exception as e:
            print(f"Error deleting request: {e}")

    @response_app.command("create", help="Create a new response class.")
    def response_create(name: str):
        try:
            service = ResponseService(name)
            service.create_response_file()
        except Exception as e:
            print(f"Error creating response: {e}")

    @response_app.command("delete", help="Delete an existing response class.")
    def response_delete(name: str):
        try:
            service = ResponseService(name)
            service.delete_response_file()
        except Exception as e:
            print(f"Error deleting response: {e}")

    @infra_app.command("sqs", help="Add sqs service.")
    def create_sqs(
        name: str = typer.Argument(..., help="Name of the SQS queue."),
        type: str = typer.Option(
            "standard",
            help="Type of the SQS queue (standard or fifo).",
            show_default=True,
        ),
        dlq: bool = typer.Option(
            False, help="Create a Dead Letter Queue (DLQ)."
        ),
    ):
        try:
            infra_service = InfrastructureService()
            name = infra_service.create_sqs_queue(
                queue_type="sqs", name=name, type=type, dlq=dlq
            )
            typer.echo(
                f"Queue '{name}' created successfully with sqs type '{type}'."
            )
        except Exception as e:
            print(f"Error creating SQS queue: {e}")

    @infra_app.command("dlq", help="Add dlq service")
    def create_dlq(
        name: str = typer.Argument(
            ..., help="Name of the DLQ (Dead Letter Queue)."
        ),
        type: str = typer.Option(
            "standard",
            help="Type of the SQS queue (standard or fifo).",
            show_default=True,
        ),
    ):
        try:
            infra_service = InfrastructureService()
            name = infra_service.create_sqs_queue("dlq", name, type)
            typer.echo(
                f"Queue '{name}' created successfully with sqs type '{type}'."
            )
        except Exception as e:
            print(f"Error creating DLQ: {e}")

    @ecs_app.command("list-clusters", help="List all ECS clusters.")
    def list_clusters():
        try:
            ecs_client = boto3.client("ecs")
            response = ecs_client.list_clusters()
            clusters = response.get("clusterArns", [])
            if clusters:
                typer.echo("ECS Clusters:")
                for cluster in clusters:
                    typer.echo(f"- {cluster}")
            else:
                typer.echo("No ECS clusters found.")
        except Exception as e:
            typer.echo(f"Error listing ECS clusters: {e}")

    @ecs_app.command(
        "list-tasks", help="List all ECS tasks in a specified cluster."
    )
    def list_tasks(
        cluster: str = typer.Option(
            ..., "--cluster", "-c", help="The name of the ECS cluster."
        )
    ):
        try:
            ecs_client = boto3.client("ecs")
            response = ecs_client.list_tasks(cluster=cluster)
            tasks = response.get("taskArns", [])
            if tasks:
                typer.echo(f"ECS Tasks in cluster '{cluster}':")
                for task in tasks:
                    typer.echo(f"- {task}")
            else:
                typer.echo(f"No tasks found in cluster '{cluster}'.")
        except Exception as e:
            typer.echo(f"Error listing ECS tasks: {e}")

    @ecs_app.command("describe-cluster", help="Describe an ECS cluster.")
    def describe_cluster(
        cluster: str = typer.Option(
            ..., "--cluster", "-c", help="The name of the ECS cluster."
        )
    ):
        try:
            ecs_client = boto3.client("ecs")
            response = ecs_client.describe_clusters(clusters=[cluster])
            clusters = response.get("clusters", [])
            if clusters:
                typer.echo(f"Description of ECS cluster '{cluster}':")
                for cluster_info in clusters:
                    typer.echo(cluster_info)
            else:
                typer.echo(f"No description found for cluster '{cluster}'.")
        except Exception as e:
            typer.echo(f"Error describing ECS cluster: {e}")

    @ecs_app.command("describe-task", help="Describe an ECS task.")
    def describe_task(
        cluster: str = typer.Option(
            ..., "--cluster", "-c", help="The name of the ECS cluster."
        ),
        task: str = typer.Option(
            ..., "--task", "-t", help="The ARN of the ECS task."
        ),
    ):
        try:
            ecs_client = boto3.client("ecs")
            response = ecs_client.describe_tasks(cluster=cluster, tasks=[task])
            tasks = response.get("tasks", [])
            if tasks:
                typer.echo(
                    f"Description of ECS task '{task}' in cluster '{cluster}':"
                )
                for task_info in tasks:
                    typer.echo(task_info)
            else:
                typer.echo(
                    f"No description found for task '{task}' in cluster '{cluster}'."
                )
        except Exception as e:
            typer.echo(f"Error describing ECS task: {e}")

    @ecs_app.command("stop-task", help="Stop an ECS task.")
    def stop_task(
        cluster: str = typer.Option(
            ..., "--cluster", "-c", help="The name of the ECS cluster."
        ),
        task: str = typer.Option(
            ..., "--task", "-t", help="The ARN of the ECS task."
        ),
    ):
        try:
            ecs_client = boto3.client("ecs")
            response = ecs_client.stop_task(cluster=cluster, task=task)
            typer.echo(f"Stopped task '{task}' in cluster '{cluster}'.")
        except Exception as e:
            typer.echo(f"Error stopping ECS task: {e}")

    @ecs_app.command(
        "stop-all-tasks", help="Stop all ECS tasks in a specified cluster."
    )
    def stop_all_tasks(
        cluster: str = typer.Option(
            ..., "--cluster", "-c", help="The name of the ECS cluster."
        )
    ):
        try:
            ecs_client = boto3.client("ecs")
            response = ecs_client.list_tasks(cluster=cluster)
            tasks = response.get("taskArns", [])
            if tasks:
                for task in tasks:
                    ecs_client.stop_task(cluster=cluster, task=task)
                    typer.echo(f"Stopped task '{task}' in cluster '{cluster}'.")
            else:
                typer.echo(f"No tasks found in cluster '{cluster}'.")
        except Exception as e:
            typer.echo(f"Error stopping ECS tasks: {e}")

    @env_app.command("setup", help="Setup environment variables.")
    def env_setup():
        current_dir = os.getcwd()
        env_example_file = os.path.join(current_dir, ".env.example")
        env_file = os.path.join(current_dir, ".env")
        if os.path.exists(env_file):
            typer.echo("Environment file already exists.")
            return
        if not os.path.exists(env_example_file):
            typer.echo(
                "Error: '.env.example' file is missing in the current working directory."
            )
            return
        try:
            shutil.copy(env_example_file, env_file)
            typer.echo("Environment file created successfully.")
        except Exception as e:
            typer.echo(f"Error creating environment file: {e}")

    @env_app.command(
        "get", help="Get the environment variables of specified lambda."
    )
    def get_env(
        lambda_name: str = typer.Option(
            ..., "--function", "-f", help="The name of the lambda function."
        ),
        output_format: str = typer.Option(
            "env",
            "--output",
            "-o",
            help="Output format (json or env).",
        ),
    ):
        try:
            lambda_client = boto3.client("lambda")
            response = lambda_client.get_function_configuration(
                FunctionName=lambda_name
            )
            env_vars = response.get("Environment", {}).get("Variables", {})
            env_vars = dict(sorted(env_vars.items()))
            if env_vars:
                if output_format == "json":
                    import json

                    print(json.dumps(env_vars, indent=4))
                elif output_format == "env":
                    for key, value in env_vars.items():
                        print(f"{key}={value}")
            else:
                typer.echo(
                    f"No environment variables found for '{lambda_name}'."
                )
        except Exception as e:
            print(f"Error getting environment variables: {e}")

    def validate_s3_uri(uri: str) -> bool:
        return uri.startswith("s3://") and len(uri.split("/", 3)) >= 4

    def submit_glue_job(operation: str, source_uri: str, dest_uri: str):
        glue = boto3.client("glue")
        try:
            response = glue.start_job_run(
                JobName="spartan-data-job",
                Arguments={
                    "--operation": operation,
                    "--source_uri": source_uri,
                    "--dest_uri": dest_uri,
                },
            )
            typer.echo(
                f"Triggered Glue job for '{operation}' from {source_uri} to {dest_uri}. JobRunId: {response['JobRunId']}"
            )
        except botocore.exceptions.ClientError as e:
            typer.echo(f"Error submitting Glue job: {e}")

    @debug_app.command("init", help="Create a VS Code launch.json")
    def debug_init():
        option = questionary.select(
            "Select debug configuration:", choices=DEBUG_OPTIONS
        ).ask()
        if not option:
            typer.echo("Operation cancelled.")
            raise typer.Exit(1)

        service = DebugService()
        service.create_launch_json(option)

    @app.command(
        "init",
        help="Initialize a new Spartan project with a starter kit.",
    )
    def app_create(project_name: str):
        template = questionary.select(
            "Select a Starter Kit:",
            choices=TEMPLATE_OPTIONS,
        ).ask()

        if template is None:
            typer.echo("Operation cancelled.")
            raise typer.Exit(1)

        template = template.lower().replace(" ", "-")

        if template == "quit":
            typer.echo("Exiting the application creation process.")
            raise typer.Exit(0)

        template_name = f"spartan-native-{template}"
        creator = ApplicationService(project_name, template_name=template_name)
        creator.create_app()
        typer.echo(
            f"✅ Project '{project_name}' created with template '{template_name}'"
        )
        typer.echo("✅ Spartan, your project is ready to go!")


def run_poetry_command(command):
    try:
        result = subprocess.run(
            ["poetry", command], capture_output=True, text=True, check=True
        )

        print(result.stdout)

    except subprocess.CalledProcessError as e:
        print("Error:", e)
        print("Command output:", e.output)


def is_valid_folder_name(name):
    """
    Check if a given string is a valid folder name.
    """

    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-")

    return all(char in valid_chars for char in name)


register_commands()


def main():
    try:
        app()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user (Ctrl+C). Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
