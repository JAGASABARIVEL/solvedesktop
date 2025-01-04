from datetime import datetime
from flask import request, jsonify
from flask_cors import cross_origin

from database_schema import Project, Task, TaskHistory, TaskComment, User

from Features.Tasks import Consumer

TOPIC = "task"
GRP_ID = "task-grp"
BOOTSTRAP_SERVER = "localhost:9092"


def init_endpoint(app_context, app, Session):
    with app_context:
        #def start_consumer():
        #    Consumer(app, topic=TOPIC, group_id=GRP_ID, bootstrap_servers=BOOTSTRAP_SERVER, session=Session).run()
        ## Start the consumer in a separate thread
        #consumer_thread = Thread(target=start_consumer, daemon=True)
        #consumer_thread.start()

        # Endpoints
        @app.route('/projects/ping', methods=['GET'])
        @cross_origin()
        def ping_project_service():
            return jsonify({"message": "Projects service is alive"}), 200

        # === Project Endpoints ===
        @app.route('/projects', methods=['POST'])
        @cross_origin()
        def create_project():
            data = request.json
            project_name = data.get("name")
            description = data.get('description')
            organization_id = data.get('organization_id')
            creator_id = data.get('creator_id')
            if not project_name or not organization_id or not creator_id:
                return jsonify({"error": "Missing required fields"}), 400
            with Session() as session:
                project = session.query(Project).filter_by(name=project_name).first()
                if project:
                    return jsonify({"error": "Project already exists"}), 409
                project = Project(
                    name=project_name,
                    description=description,
                    organization_id=organization_id,
                    creator_id=creator_id
                )
                session.add(project)
                session.commit()
                return jsonify(project.to_dict()), 201
        
        @app.route('/projects', methods=['GET'])
        @cross_origin()
        def get_all_projects():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({"error": "Missing Organization"}), 400
            with Session() as session:
                projects = [project.to_dict() for project in session.query(Project).filter_by(organization_id=organization_id).all()]
            return jsonify(projects), 200
        
        @app.route('/projects/<project_id>', methods=['GET'])
        @cross_origin()
        def get_project(project_id):
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                return jsonify(project.to_dict()), 200
        
        @app.route('/projects/<project_id>', methods=['PATCH'])
        @cross_origin()
        def update_project(project_id):
            data = request.json
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                project.name = data.get("name", project.name)
                project.description = data.get("description", project.description)
            return jsonify(project), 200
        
        @app.route('/projects/<project_id>', methods=['DELETE'])
        @cross_origin()
        def delete_project(project_id):
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                session.delete(project)
                session.commit()
        
        # === Task Endpoints ===
        @app.route('/projects/<project_id>/tasks', methods=['POST'])
        @cross_origin()
        def create_task(project_id):
            data = request.json
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                task = Task(
                    organization_id = project.organization_id,
                    project_id = project.id,
                    title=data.get("title"),
                    description=data.get("description"),
                    priority=data.get("priority"),
                    creator_id=data.get("creator_id"),
                    assignee_id=data.get("assignee"),
                    status='new'
                )
                session.add(task)
                session.commit()
                return jsonify(task.to_dict()), 201

        
        @app.route('/projects/<project_id>/tasks', methods=['GET'])
        @cross_origin()
        def get_tasks(project_id):
            # TODO: Auth - Only the user who request should be part of this org
            # and should have loged in
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                tasks = [task.to_dict() for task in session.query(Task).filter_by(project_id=project_id).all()]
            return jsonify(tasks), 200

        @app.route('/projects/<project_id>/tasks/<task_id>', methods=['GET'])
        @cross_origin()
        def get_task(project_id, task_id):
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                task = session.query(Task).get(task_id)
                if not task:
                    return jsonify({"error": "Task not found in this project"}), 404
                assignee_name = ''
                assignee_user = session.query(User).get(task.assignee_id)
                if assignee_user:
                    assignee_name = assignee_user.name
                created_user_name = ''
                created_user = session.query(User).get(task.creator_id)
                if created_user:
                    created_user_name = created_user.name
                response = task.to_dict()
                response.update({"assignee": assignee_name, "created_by_name": created_user_name})
                return jsonify(response), 200
        
        @app.route('/projects/<project_id>/tasks/<task_id>', methods=['PATCH'])
        @cross_origin()
        def update_task(project_id, task_id):
            data = request.json
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                task = session.query(Task).get(task_id)
                if not task:
                    return jsonify({"error": "Task not found in this project"}), 404
                task.title = data.get("title", task.title)
                task.description = data.get("description", task.description)
                task.priority = data.get("priority", task.priority)
                task.assignee_id = data.get("assignee", task.assignee_id)
                task.status = data.get("status", task.status)
                session.commit()
                return jsonify(task.to_dict()), 200
        
        @app.route('/projects/<project_id>/tasks/<task_id>', methods=['DELETE'])
        @cross_origin()
        def delete_task(project_id, task_id):
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                task = session.query(Task).get(task_id)
                if not task:
                    return jsonify({"error": "Task not found in this project"}), 404
                session.delete(task)
                session.commit()
                return jsonify({"message": "Task deleted successfully"}), 200
        
        @app.route('/projects/<project_id>/tasks/<task_id>/history', methods=['GET', 'POST'])
        @cross_origin()
        def task_history(project_id, task_id):
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                if not task_id:
                    return jsonify({"error": "task_id is required"}), 400
                if request.method == 'GET':
                    # Get task history by task_id
                    task_history = session.query(TaskHistory).filter_by(task_id=task_id).all()
                    return jsonify([
                        history.to_dict() for history in task_history
                    ])
                elif request.method == 'POST':
                    data = request.get_json()
                    task_id = data.get('task_id')
                    user_id = data.get('user_id')
                    action = data.get('action')
                    details = data.get('details')
                    if not task_id or not action:
                        return jsonify({'error': 'task_id and action are required'}), 400
                    new_history = TaskHistory(
                        task_id=task_id,
                        user_id=user_id,
                        action=action,
                        details=details
                    )
                    session.add(new_history)
                    session.commit()
                    return jsonify(new_history.to_dict()), 201

        @app.route('/projects/<project_id>/tasks/<task_id>/comment', methods=['GET', 'POST'])
        @cross_origin()
        def task_comment(project_id, task_id):
            with Session() as session:
                project = session.query(Project).get(project_id)
                if not project:
                    return jsonify({"error": "Project not found"}), 404
                if request.method == 'GET':
                    comments = TaskComment.query.filter_by(task_id=task_id).all()
                    response = []
                    for comment in comments:
                        temp = comment.to_dict()
                        commented_user_name = session.query(User).filter_by(id=comment.user_id).first().name
                        temp.update({'user_name': commented_user_name})
                        response.append(temp)
                    return jsonify(response)
                elif request.method == 'POST':
                    data = request.json
                    user_id = data.get('user_id')
                    comment_body = data.get('comment_body')
                    if not user_id or not comment_body:
                        return jsonify({'error': 'user_id, and comment_body are required'}), 400
                    new_comment = TaskComment(
                        task_id=task_id,
                        user_id=user_id,
                        comment_body=comment_body
                    )
                    session.add(new_comment)
                    session.commit()
                    commented_user_name = session.query(User).filter_by(id=new_comment.user_id).first().name
                    response = new_comment.to_dict()
                    response.update({'user_name': commented_user_name})
                    return jsonify(), 201
    return app
                        