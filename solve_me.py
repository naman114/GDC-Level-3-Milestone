from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs


class TasksCommand:
    TASKS_FILE = "tasks.txt"
    COMPLETED_TASKS_FILE = "completed.txt"

    current_items = {}
    completed_items = []

    def read_current(self):
        try:
            file = open(self.TASKS_FILE, "r")
            for line in file.readlines():
                item = line[:-1].split(" ")
                self.current_items[int(item[0])] = " ".join(item[1:])
            file.close()
        except Exception:
            pass

    def read_completed(self):
        try:
            file = open(self.COMPLETED_TASKS_FILE, "r")
            self.completed_items = file.readlines()
            file.close()
        except Exception:
            pass

    def write_current(self):
        with open(self.TASKS_FILE, "w+") as f:
            f.truncate(0)
            for key in sorted(self.current_items.keys()):
                f.write(f"{key} {self.current_items[key]}\n")

    def write_completed(self):
        with open(self.COMPLETED_TASKS_FILE, "w+") as f:
            f.truncate(0)
            for item in self.completed_items:
                f.write(f"{item}\n")

    def runserver(self):
        address = "127.0.0.1"
        port = 8000
        server_address = (address, port)
        httpd = HTTPServer(server_address, TasksServer)
        print(f"Started HTTP Server on http://{address}:{port}")
        httpd.serve_forever()

    def run(self, command, args):
        self.read_current()
        self.read_completed()
        if command == "add":
            self.add(args)
        elif command == "done":
            self.done(args)
        elif command == "delete":
            self.delete(args)
        elif command == "ls":
            self.ls()
        elif command == "report":
            self.report()
        elif command == "runserver":
            self.runserver()
        elif command == "help":
            self.help()

    def help(self):
        print(
            """Usage :-
$ python tasks.py add 2 hello world # Add a new item with priority 2 and text "hello world" to the list
$ python tasks.py ls # Show incomplete priority list items sorted by priority in ascending order
$ python tasks.py del PRIORITY_NUMBER # Delete the incomplete item with the given priority number
$ python tasks.py done PRIORITY_NUMBER # Mark the incomplete item with the given PRIORITY_NUMBER as complete
$ python tasks.py help # Show usage
$ python tasks.py report # Statistics
$ python tasks.py runserver # Starts the tasks management server"""
        )

    def add(self, args):
        priority = int(args[0])
        task = args[1]
        if priority in self.current_items.keys():
            for key in sorted(self.current_items.keys(), reverse=True):
                self.current_items[key + 1] = self.current_items[key]
                if key == priority:
                    break

        self.current_items[priority] = task
        self.write_current()
        return f'Added task: "{task}" with priority {priority}'

    def done(self, args):
        args[0] = int(args[0])
        if args[0] in self.current_items:
            self.completed_items.append(self.current_items[args[0]])
            self.current_items.pop(args[0])
            self.write_current()
            # Removing "\n" from all completed_items
            for i in range(len(self.completed_items)):
                self.completed_items[i] = self.completed_items[i].rstrip("\n")
            self.write_completed()
            return "Marked item as done."
        else:
            return f"Error: no incomplete item with priority {args[0]} exists."

    def delete(self, args):
        args[0] = int(args[0])
        if args[0] in self.current_items:
            self.current_items.pop(args[0])
            self.write_current()
            return f"Deleted item with priority {args[0]}"
        else:
            return (
                f"Error: item with priority {args[0]} does not exist. Nothing deleted."
            )

    def ls(self):
        for idx, task in enumerate(self.current_items.items()):
            print(f"{idx + 1}. {task[1]} [{task[0]}]")

    def report(self):
        print(f"Pending : {len(self.current_items)}")
        self.ls()

        print(f"\nCompleted : {len(self.completed_items)}")
        for idx, task in enumerate(self.completed_items):
            print(f"{idx + 1}. {task}")

    # Endpoint: /tasks
    # Renders the pending tasks as a table
    def render_pending_tasks(self):
        pending_tasks_html = f"""
        <div style="display: flex; flex-direction: column; align-items: center">
            <h1>Incomplete Tasks</h1>

            <table style="border: 1px solid black">
                <tr style="border: 1px solid black">
                    <th style="border: 1px solid black; padding: 10px">Priority</th>
                    <th style="border: 1px solid black; padding: 10px">Task Name</th>
                </tr>

                {self.generate_table_rows_html("pending")}
            </table>
        </div>
        """
        return pending_tasks_html

    # Endpoint: /completed
    # Renders the completed tasks as a table
    def render_completed_tasks(self):
        completed_tasks_html = f"""
        <div style="display: flex; flex-direction: column; align-items: center">
            <h1>Completed Tasks</h1>

            <table style="border: 1px solid black">
                <tr style="border: 1px solid black">
                    <th style="border: 1px solid black; padding: 10px">Task Name</th>
                </tr>

                {self.generate_table_rows_html("completed")}
            </table>
        </div>
        """
        return completed_tasks_html

    # Helper function to return the rows of the 'pending tasks' and 'completed tasks' tables
    def generate_table_rows_html(self, task_type):
        self.current_items.clear()
        self.read_current()
        self.read_completed()
        html = ""
        if task_type == "pending":
            for key in sorted(self.current_items.keys()):
                task = self.current_items[key]
                html += f"""
                        <tr>
                            <td style="border: 1px solid black; padding: 10px">{key}</td>
                            <td style="border: 1px solid black; padding: 10px">{task}</td>
                        </tr>                        
                        """
        elif task_type == "completed":
            for task in self.completed_items:
                html += f"""
                        <tr>
                            <td style="border: 1px solid black; padding: 10px">{task}</td>
                        </tr>                        
                        """
        return html

    # Endpoint: /manage
    # Renders the page to manage tasks i.e. add, delete or complete tasks
    def render_manage_tasks(self):
        with open("manage.html", "r", encoding="utf-8") as f:
            manage_html = f.read()
            return manage_html


class TasksServer(TasksCommand, BaseHTTPRequestHandler):
    def do_GET(self):
        task_command_object = TasksCommand()
        if self.path == "/tasks":
            content = task_command_object.render_pending_tasks()
        elif self.path == "/completed":
            content = task_command_object.render_completed_tasks()
        elif self.path == "/manage":
            content = task_command_object.render_manage_tasks()
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode())

    def do_POST(self):
        task_command_object = TasksCommand()

        content_length = int(self.headers["Content-Length"])
        body = parse_qs(self.rfile.read(content_length).decode("utf-8"))

        if self.path == "/add_task":
            response_content = (
                "<h3>"
                + task_command_object.add([body["priority"][0], body["task"][0]])
                + "</h3>"
            )
        elif self.path == "/delete_task":
            response_content = (
                "<h3>" + task_command_object.delete([body["priority"][0]]) + "</h3>"
            )
        elif self.path == "/complete_task":
            response_content = (
                "<h3>" + task_command_object.done([body["priority"][0]]) + "</h3>"
            )

        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        self.wfile.write(response_content.encode())
