import os
import uuid
import time
import logging
import json
from datetime import datetime, timedelta
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import traceback


import pyexcel
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import cross_origin
from sqlalchemy import create_engine, UniqueConstraint
from sqlalchemy.orm import scoped_session, sessionmaker

# Ensure logging is configured for your application
logging.basicConfig(level=logging.DEBUG, filename="schedule-server.log")
logger = logging.getLogger(__name__)

# Models
app = None
db = SQLAlchemy()

def create_app():
    global app
    global db
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduling.db'  # Update with your DB URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit for file uploads

    with app.app_context():
        db.init_app(app)
        db.create_all()

        # Create a scoped session
        Session = scoped_session(sessionmaker(bind=db.engine))
        
        # Endpoints
        
        @app.route('/organization', methods=['POST'])
        def create_organization():
            with Session() as session:
                data = request.json
                try:
                    organization = Organization(
                        name=data['name'],
                        owner_id=data['owner_id']
                    )
                    session.add(organization)
                    session.commit()
                    return jsonify({"message": "Organization created successfully!"}), 201
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/organization/<int:id>', methods=['GET'])
        def get_organization(id):
            organization = Organization.query.get(id)
            if organization:
                return jsonify({
                    "id": organization.id,
                    "name": organization.name,
                    "owner_id": organization.owner_id
                })
            return jsonify({"error": "Organization not found"}), 404

        @app.route('/organization/<int:id>', methods=['PUT'])
        def update_organization(id):
            with Session() as session:
                data = request.json
                organization = Organization.query.get(id)
                if organization:
                    try:
                        if 'name' in data:
                            organization.name = data['name']
                        if 'owner_id' in data:
                            organization.owner_id = data['owner_id']
                        session.commit()
                        return jsonify({"message": "Organization updated successfully!"})
                    except Exception as e:
                        return jsonify({"error": str(e)}), 400
                return jsonify({"error": "Organization not found"}), 404

        @app.route('/organization/<int:id>', methods=['DELETE'])
        def delete_organization(id):
            with Session() as session:
                organization = Organization.query.get(id)
                if organization:
                    try:
                        session.delete(organization)
                        session.commit()
                        return jsonify({"message": "Organization deleted successfully!"})
                    except Exception as e:
                        return jsonify({"error": str(e)}), 400
                return jsonify({"error": "Organization not found"}), 404
        
        @app.route('/platforms', methods=['GET'])
        @cross_origin()
        def get_platforms():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({"error": "Organization ID is required"}), 400
            organization = Organization.query.filter_by(id=organization_id).first()
            platforms = Platform.query.filter_by(owner_id=organization.owner_id).all()
            return jsonify([{
                "id": p.id,
                "platform_name": p.platform_name,
                "status": p.status
            } for p in platforms]), 200
        
        @app.route('/platforms', methods=['POST'])
        def add_platform():
            data = request.json
            if not data.get('organization_id'):
                return jsonify({"error": "Organization ID is required"}), 400
            if not data.get('platform'):
                return jsonify({"error": "Platform is required"}), 400
            if not data.get('owner_id'):
                return jsonify({"error": "Owner ID is required"}), 400
            platform = Platform.query.filter_by(owner_id=data['owner_id'], platform_name=data['platform']).first()
            if platform:
                return jsonify({"error": "Platform already added to the organization"}), 409
            with Session() as session:
                platform = Platform(
                    owner_id=data['owner_id'],
                    platform_name=data['platform'],
                    login_credentials=data['login_credentials']
                )
                session.add(platform)
                session.commit()
                return jsonify({"message": "Platform added successfully!"}), 201

        @app.route('/platforms', methods=['PUT'])
        def update_platform():
            data = request.json
            if not data.get('platform_id'):
                return jsonify({'error': 'Platform Id is required'})
            if not data.get('user_id'):
                return jsonify({'error': 'Please login to edit the platform'})
            with Session() as session:
                platform = session.query(Platform).filter_by(id=data['platform_id']).first()
                if platform.owner_id != data['user_id']:
                    return jsonify({'error': 'Sorry! - You dont have permission'})
                if not platform:
                    return jsonify({"error": "Platform not found"}), 404
                platform.login_credentials = data['login_credentials']
                session.commit()
                return jsonify({"message": "Platform updated successfully!"}), 200

        @app.route('/platforms', methods=['DELETE'])
        def delete_platform():
            data = request.json
            if not data.get('platform_id'):
                return jsonify({'error': 'Platform Id is required'})
            if not data.get('user_id'):
                return jsonify({'error': 'Please login to edit the platform'})
            with Session() as session:
                platform = session.query(Platform).get(data['platform_id'])
                if platform.owner_id != data['user_id']:
                    return jsonify({'error': 'Sorry! - You dont have permission'})
                if not platform:
                    return jsonify({"error": "Platform not found"}), 404
                session.delete(platform)
                session.commit()
                return jsonify({"message": "Platform deleted successfully!"}), 200

        
        def signup_owner_with_organization(session, user_data, org_data, platform_data):
            with session.begin():
                # Step 1: Check for Existing Organization
                organization = session.query(Organization).filter_by(name=org_data['name']).first()
                if not organization:
                    # Create the Organization if it doesn't exist
                    organization = Organization(name=org_data['name'])
                    session.add(organization)
                    session.flush()  # Ensures organization.id is available
                # Step 2: Create or Get the OwnerAccount
                owner_account = session.query(OwnerAccount).filter_by(user_id=user_data['id']).first()
                if not owner_account:
                    # Create new OwnerAccount if not found
                    owner_account = OwnerAccount(user_id=user_data['id'], organization_id=organization.id)
                    session.add(owner_account)
                    session.flush()  # Ensures owner_account.id is available
                # Step 3: Add Platform
                platform = Platform(
                    owner_id=owner_account.id,
                    platform_name=platform_data['platform_name'],
                    login_credentials=platform_data['platform_login_credentials']
                )
                session.add(platform)
                session.commit()
                return {"message": "Signup and platform registration successful!"}


        @app.route('/signup', methods=['POST'])
        def signup():
            with Session() as session:
                data = request.json
                try:
                    user = session.query(User).filter_by(phone=data['phone']).first()
                    if user:
                        return jsonify({"error": "User already exists"}), 409
                    if data['user_type'] != "owner" and not session.query(Organization).filter_by(name=data['organization']).first():
                        return jsonify({"error": "Please contact your management team to register the Organization"}), 409
                    with session.begin_nested():
                        user = User(
                            name=data['name'],
                            phone=data['phone'],
                            email=data['email'],
                            user_type=data['user_type'],
                            password=data['password']  # Hash in production
                        )
                        session.add(user)
                        session.flush()
                        organization = session.query(Organization).filter_by(name=data['organization']).first()
                        if data['user_type'] == 'owner':
                            if not organization:
                                organization = Organization(
                                    name=data['organization'],
                                    owner_id=user.id
                                )
                                session.add(organization)
                                session.flush()
                            user.organization_id = organization.id
                            session.add(user)
                            # Create OwnerAccount
                            owner_account = session.query(OwnerAccount).filter_by(organization_id=organization.id).first()
                            if not owner_account:
                                owner_account = OwnerAccount(
                                    user_id=user.id,
                                    organization_id=organization.id
                                )
                                session.add(owner_account)
                                session.flush()
                                # Add Platform
                                platform = Platform(
                                    owner_id=owner_account.id,
                                    platform_name=data['platform_name'],
                                    login_credentials=data['platform_login_credentials']
                                )
                                session.add(platform)
                        elif data['user_type'] == 'employee':
                            user.organization_id = organization.id
                            session.add(user)
                        session.commit()
                    return jsonify({"message": "User signed up successfully!"}), 201
                except Exception as e:
                    session.rollback()
                    print (e)
                    return jsonify({"error": str(e)}), 400

        @app.route('/login', methods=['POST'])
        @cross_origin()
        def login():
            data = request.json
            user = User.query.filter_by(phone=data['phone']).first()
            if user and user.password == data['password']:  # Verify hash in production
                return jsonify({
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "role": user.user_type,
                    "organization": user.organization_id,
                }), 200
            return jsonify({"error": "Invalid credentials"}), 401

        def generate_unique_filename(original_filename):
            # Extract file extension
            file_extension = os.path.splitext(original_filename)[1]
            # Generate unique name
            unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{file_extension}"
            # Define storage directory
            storage_directory = "uploaded_files"
            os.makedirs(storage_directory, exist_ok=True)  # Create directory if it doesn't exist
            return os.path.join(storage_directory, unique_name)
        
        def save_excel_locally(file, original_filename):
            unique_filename = generate_unique_filename(original_filename)
            file.save(unique_filename)  # Save uploaded file
            return unique_filename

        ## Pandas way of doing it#
        #def process_excel_from_upload(file):
        #    excel_data = pd.read_excel(file)
        #    return excel_data.to_dict(orient='records')

        def process_excel_from_upload(file):
            print(os.path.exists(file)) 
            sheet = pyexcel.get_sheet(file_name=file)
            data = []
            headers = sheet.row[0]  # First row as headers
            for row in sheet.row[1:]:
                data.append(dict(zip(headers, row)))
            return data

        def dump_for_excel_datasource(datasource):
            excel_filenames = []
            # Handle Excel Datasource
            for key, source in datasource.items():
               if source['type'] == 'excel':
                   if source['file_upload'] in request.files:
                       file = request.files[source['file_upload']]
                       unique_filename = save_excel_locally(file, file.filename)
                       source['file_path'] = unique_filename
                       excel_filenames.append(unique_filename)
                       source['data'] = process_excel_from_upload(unique_filename)
            return excel_filenames

        @app.route('/schedule', methods=['POST'])
        @cross_origin()
        def schedule_message():
          try:
            # Fetch regular fields from form data
            organization_id = request.form.get('organization_id')
            name = request.form.get('name')
            platform = request.form.get('platform')
            user_id = request.form.get('user_id')
            recipient_type = request.form.get('recipient_type')
            recipient_id = request.form.get('recipient_id')
            message_body = request.form.get('message_body')
            scheduled_time = request.form.get('scheduled_time')
            datasource = json.loads(request.form.get('datasource', {}))  # This will be a JSON string

            # TODO: This has to be improved to compare the contacts in user/group
            # matches with the excel/database though we are checing that in the schedule job
            # while running but it would help if we could detect it earlier.
            if recipient_type == "group" and not GroupMember.query.filter_by(id=recipient_id).first():
                # Lookup agains groupid is safe since the UI will
                # provide only the valid group ID which has only
                # valid contacts
                return jsonify({"error" : "Group not found"}), 404
            
            if recipient_type == "user" and not Contact.query.filter_by(id=recipient_id).first():
                # Even here UI would do its job but we are adding extra layer of protection
                return jsonify({"error" : "Contact not found"}), 404

            if not organization_id:
                return jsonify({"error": "Organization ID is required"}), 400
            if not platform:
                return jsonify({"error": "Platform is required"}), 400
            organization = Organization.query.filter_by(id=organization_id).first()
            platform = Platform.query.filter_by(owner_id=organization.owner_id, id=platform).first()
            if not platform:
                return jsonify({"error": "Platform not registered with the organization"}), 404
            with Session() as session:
                try:
                    excel_filenames = dump_for_excel_datasource(datasource)
                    print(excel_filenames)
                    message = ScheduledMessage(
                        user_id=user_id,
                        name=name,
                        recipient_type=recipient_type,
                        recipient_id=recipient_id,
                        message_body=message_body,
                        platform=platform.id,
                        organization_id=organization_id,
                        datasource=datasource,  # Store the entire datasource configuration
                        excel_filename=",".join(excel_filenames),  # Store filenames as comma-separated string
                        scheduled_time=datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                    )
                    session.add(message)
                    session.commit()
                    return jsonify({"message": "Message scheduled successfully!"}), 201
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
          except Exception as ex:
            logging.info(str(traceback.format_exc()))

        @app.route('/schedule', methods=['GET'])
        @cross_origin()
        def get_all_schedules():
            organization_id = request.args.get("organization_id")
            if not organization_id:
                return jsonify({"error": "Organization ID is required"}), 400
            recipient_type = request.args.get("recipient_type")
            recipient_id = request.args.get("recipient_id") # Group name or customer name
            if recipient_type and not recipient_id:
                return jsonify({"error" : "Can not lookup without recipient/group name"})
            try:
                with Session() as session:
                    schedule_query = session.query(ScheduledMessage)
                    schedules = None
                    if recipient_id and recipient_type:
                        schedules = schedule_query.filter_by(
                            organization_id=organization_id,
                            recipient_type=recipient_type,
                            recipient_id=recipient_id
                        ).all()
                    else:
                        schedules = schedule_query.filter_by(
                            organization_id=organization_id
                        ).all()
                    response = []
                    for schedule in schedules:
                        recipient_name, platform_name = "", ""
                        if schedule.recipient_type == "group":
                            group = session.query(ContactGroup).filter_by(id=schedule.recipient_id).first()
                            recipient_name = group.name
                        elif schedule.recipient_type == "user":
                            contact = session.query(Contact).filter_by(id=schedule.recipient_id).first()
                            recipient_name = contact.name
                        
                        platform = session.query(Platform).filter_by(id=schedule.platform).first()
                        platform_name = platform.platform_name

                        created_by = session.query(User).filter_by(id=schedule.user_id).first().name
                        response.append({
                            "id": schedule.id,
                            "name": schedule.name,
                            "recipient_name": recipient_name,
                            "recipient_type": schedule.recipient_type,
                            "platform_name": platform_name,
                            "created_by": created_by,
                            "created_at": schedule.created_at.isoformat(),
                            "frequency": schedule.frequency,
                            "message_body": schedule.message_body,
                        })
                    return jsonify(response), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @app.route('/schedule/<int:schedule_id>', methods=['GET'])
        def get_schedule(schedule_id):
            try:
                with Session() as session:
                    schedule = session.query(ScheduledMessage).get(schedule_id)
                    if not schedule:
                        return jsonify({"error": "Schedule not found"}), 404
                    
                    response = {
                        "id": schedule.id,
                        "name": schedule.name,
                        "user_id": schedule.user_id,
                        "recipient_type": schedule.recipient_type,
                        "recipient_id": schedule.recipient_id,
                        "message_body": schedule.message_body,
                        "scheduled_time": schedule.scheduled_time.isoformat(),
                        "datasource": schedule.datasource,  # Ensure it's stored as JSON in DB
                        "status": schedule.status
                    }
                    return jsonify(response), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        def delete_files(filepaths):
            for filepath in filepaths:
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        @app.route('/schedule/<int:schedule_id>', methods=['PUT'])
        def update_schedule(schedule_id):
            platform = request.form.get('platform')
            recipient_type = request.form.get('recipient_type')
            recipient_id = request.form.get('recipient_id')
            message_body = request.form.get('message_body')
            scheduled_time = request.form.get('scheduled_time')
            datasource = request.form.get('datasource', {})  # This will be a JSON string
            datasource = json.loads(datasource) if datasource else {}
            try:
                with Session() as session:
                    schedule = session.query(ScheduledMessage).get(schedule_id)
                    if not schedule:
                        return jsonify({"error": "Schedule not found"}), 404
                    # Check if the current Excel file and delete it
                    if datasource and schedule.excel_filename:
                        try:
                            delete_files(schedule.excel_filename.split(','))
                        except Exception as file_remove_exception:
                            logging.error(str(file_remove_exception))
                            return jsonify({"error": "Can not remove the existing file"}), 400
                    # Update fields
                    if message_body:
                        schedule.message_body = message_body
                    if scheduled_time:
                        schedule.scheduled_time = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                    if datasource:
                        schedule.datasource = datasource  # Ensure this is JSON serializable
                        excel_filenames = dump_for_excel_datasource(datasource)
                        schedule.excel_filename=",".join(excel_filenames)
                    if platform:
                        schedule.platform = platform
                    if recipient_type and recipient_id:
                        schedule.recipient_id = recipient_id
                        schedule.recipient_type = recipient_type
                    session.commit()
                    return jsonify({"message": "Schedule updated successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400


        @app.route('/schedule/<int:schedule_id>', methods=['DELETE'])
        def delete_schedule(schedule_id):
            with Session() as session:
                try:
                    msg = session.query(ScheduledMessage).get(schedule_id)
                    if not msg:
                        return jsonify({"error": "Scheduled message not found"}), 404
                    # Delete associated Excel files
                    if msg.excel_filename:
                        delete_files(msg.excel_filename.split(','))
                    msg.status = 'cancelled'
                    #session.delete(msg)
                    session.commit()
                    return jsonify({"message": "Scheduled message deleted successfully!"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/schedule/restart/<int:schedule_id>', methods=['PUT'])
        def restart_schedule(schedule_id):
            with Session() as session:
                try:
                    msg = session.query(ScheduledMessage).get(schedule_id)
                    if not msg:
                        return jsonify({"error": "Scheduled message not found"}), 404
                    if msg.status == 'scheduled':
                        return jsonify({"error": "Already scheduled"}), 404
                    if msg.status == 'in-progress':
                        return jsonify({"error": "Scheduled is running and cannot be restarted at this moment"}), 404
                    msg.status = 'scheduled'
                    session.commit()
                    return jsonify({"message": "Scheduled message restarted successfully!"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/contacts', methods=['POST'])
        @cross_origin()
        def add_contact():
            data = request.json
            contact = Contact.query.filter_by(phone=data['phone'], organization_id=data['organization_id']).first()
            if contact:
                return jsonify({"error": "Contact is already existing"}), 409

            with Session() as session:
                try:
                    contact = Contact(
                        name=data['name'],
                        phone=data['phone'],
                        created_by=data['created_by'],
                        organization_id=data['organization_id']
                    )
                    session.add(contact)
                    session.commit()
                    return jsonify({"message": "Contact added successfully!"}), 201
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
        
        @app.route('/contacts', methods=['GET'])
        @cross_origin()
        def get_contacts():
            # Get the query parameters
            organization_id = request.args.get('organization_id')
            page = request.args.get('page', type=int)
            per_page = request.args.get('per_page', type=int, default=10)
            if not organization_id:
                return jsonify({"error" : "Organization ID is required"}), 400
            # Filter the contacts by organization_id
            query = Contact.query
            if organization_id:
                query = query.filter_by(organization_id=organization_id)
            # Check if pagination is needed
            if page:
                contacts = query.paginate(page=page, per_page=per_page).items
            else:
                contacts = query.all()  # Fetch all results if no pagination
            # Format the results
            result = [{"id": c.id, "name": c.name, "phone": c.phone, "created_by": c.created_by} for c in contacts]
            return jsonify(result), 200
        
        @app.route('/contacts/<int:organization_id>', methods=['GET'])
        def get_contact_id_from_phone(organization_id):
            # Get the query parameters for the phone number
            result = Contact.query.filter_by(phone=request.args.get('phone'), organization_id=organization_id).first()
            return jsonify({"id": result.id, "name": result.name, "phone": result.phone, "created_by": result.created_by})

        @app.route('/contacts', methods=['PUT'])
        @cross_origin()
        def edit_contact():
            contact_id = request.args.get('contact_id')
            if not contact_id:
                return jsonify({"error": "Contact ID is required"}), 400
            data = request.json
            try:
                with Session() as session:
                    # Query the contact within the session context
                    contact = session.query(Contact).get(contact_id)
                    if not contact:
                        return jsonify({"error": "Contact not found"}), 404
                    # Update fields
                    contact.name = data.get('name', contact.name)
                    contact.phone = data.get('phone', contact.phone)
                    # Commit the changes
                    session.commit()
                return jsonify({"message": "Contact updated successfully!"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400


        @app.route('/contacts', methods=['DELETE'])
        @cross_origin()
        def delete_contact():
            contact_id = request.args.get('contact_id')
            if not contact_id:
                return jsonify({"error": "Contact ID is required"}), 400
            with Session() as session:
                contact = session.query(Contact).get(contact_id)
                try:
                    session.delete(contact)
                    session.commit()
                    return jsonify({"message": "Contact deleted successfully!"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/groups', methods=['POST'])
        @cross_origin()
        def create_group():
            data = request.json
            group = ContactGroup.query.filter_by(name=data['name'], organization_id=data['organization_id']).first()
            if group:
                return jsonify({"error": "Group with this name already existing"}), 409
            with Session() as session:
                try:
        		    # TODO: Confirm if the group is already existing
                    group = ContactGroup(name=data['name'], organization_id=data['organization_id'], created_by=data['created_by'])
                    session.add(group)
                    session.commit()
                    return jsonify({"id": group.id}), 201
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/groups', methods=['GET'])
        @cross_origin()
        def get_groups():
            # Get the query parameters
            organization_id = request.args.get('organization_id')
            page = request.args.get('page', type=int)
            per_page = request.args.get('per_page', type=int, default=10)
            if not organization_id:
                return jsonify({"error" : "Organization ID is required"}), 400
            # Filter the contacts by organization_id
            query = ContactGroup.query.filter_by(organization_id=organization_id)
            # Check if pagination is needed
            if page:
                groups = query.paginate(page=page, per_page=per_page).items
            else:
                groups = query.all()  # Fetch all results if no pagination
            # Format the results
            result = [{"id": g.id, "name": g.name, "created_by": g.created_by} for g in groups]
            return jsonify(result), 200

        @app.route('/groups/<int:organization_id>', methods=['GET'])
        def get_group_id_from_group_name(organization_id):
            # Get the query parameters for the phone number
            result = ContactGroup.query.filter_by(name=request.args.get('group_name'), organization_id=organization_id).first()
            print(result)
            return jsonify({"id": result.id, "name": result.name, "created_by": result.created_by})

        @app.route('/groups', methods=['PUT'])
        def update_group():
            group_id = request.args.get('group_id')
            
            if not group_id:
                return jsonify({"error": "Group ID is required"}), 400
            organization_id = request.args.get("organization_id")
            if not organization_id:
                return jsonify({"error": "Organization ID is required"}), 400
            data = request.json
            with Session() as session:
                group = session.query(ContactGroup).filter_by(id=group_id, organization_id=organization_id).first()
                try:
                    group.name = data.get('name', group.name)
                    session.commit()
                    return jsonify({"message": "Group updated successfully!"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/groups', methods=['DELETE'])
        @cross_origin()
        def delete_group():
            group_id = request.args.get('group_id')
            if not group_id:
                return jsonify({"error": "Group ID is required"}), 400
            organization_id = request.args.get("organization_id")
            if not organization_id:
                return jsonify({"error": "Organization ID is required"}), 400
            
            with Session() as session:
                group = session.query(ContactGroup).filter_by(id=group_id, organization_id=organization_id).first()
                try:
                    session.delete(group)
                    session.commit()
                    return jsonify({"message": "Group deleted successfully!"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/groups/add_contact', methods=['POST'])
        @cross_origin()
        def add_contact_to_group():
            with Session() as session:
                data = request.json
                logging.info("Data %s", data)
                try:
                    # Check if the contact exists
                    organization_id = data['organization_id']
                    contact_id = data['contact_id']
                    group_id = data['group_id']
                    contact = Contact.query.get_or_404(contact_id)
                    if not contact:
                        
                        return jsonify({"error": "Contact does not exist"}), 404
                    # Check if the contact is already a member of the group
                    existing_member = GroupMember.query.filter_by(group_id=group_id, contact_id=contact_id, organization_id=organization_id).first()
                    if existing_member:
                        return jsonify({"error": "Contact is already a member of the group"}), 400
                    # Add the contact to the group
                    group_member = GroupMember(
                        group_id=group_id, organization_id=organization_id, contact_id=contact_id
                    )
                    session.add(group_member)
                    session.commit()
                    return jsonify({"message": "Contact added to the group successfully!"}), 201
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
        
        @app.route('/groups/members', methods=['GET'])
        def get_group_members():
            group_id = request.args.get('group_id')
            if not group_id:
                return jsonify({"error": "Group ID is required"}), 400
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({"error": "Organization ID is required"}), 400
            try:
                # Query group members by group_id and organization_id
                members = GroupMember.query.filter_by(group_id=group_id, organization_id=organization_id).all()
                if not members:
                    return jsonify({"message": "No members found for this group and organization."}), 404
                # Prepare the response
                result = [
                    {
                        "id": member.id,
                        "group_id": member.group_id,
                        "contact_id": member.contact_id,
                        "organization_id": member.organization_id,
                        "created_at": member.created_at
                    }
                    for member in members
                ]
                return jsonify(result), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        @app.route('/groups/remove_contact', methods=['DELETE'])
        def remove_contact_from_group():
            group_id = request.args.get('group_id')
            if not group_id:
                return jsonify({"error": "Group ID is required"}), 400
            with Session() as session:
                data = request.json
                try:
                    # Check if the group exists
                    group = ContactGroup.query.get_or_404(group_id)
                    if not group:
                        return jsonify({"error": "Group does not exist"}), 404
                    # Check if the contact is part of the group
                    organization_id = data['organization_id']
                    contact_id = data['contact_id']
                    group_member = session.query(GroupMember).filter_by(group_id=group_id, contact_id=contact_id, organization_id=organization_id).first()
                    if not group_member:
                        return jsonify({"error": "Contact is not a member of the group"}), 400
                    # Remove the contact from the group
                    session.delete(group_member)
                    session.commit()
                    return jsonify({"message": "Contact removed from the group successfully!"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

        @app.route('/ping', methods=["GET"])
        def ping():
            return jsonify({"message": "Service is alive"}), 200

        # Placeholder for platform-specific message sending
        def send_message(platform_id, recipient_id, message_body):
            with Session() as session:
                try:
                    platform = session.query(Platform).filter_by(id=platform_id).first()
                    platform_name = platform.platform_name
                    platform_login_credentials = platform.login_credentials
                    phone_number = session.query(Contact.phone).filter_by(id=recipient_id).first()[0]
                    #TODO: Fetch credetials for the specific platform as well
                    if platform_name == 'whatsapp':
                        # Add WhatsApp API integration logic here
                        print(
                            "Message Sent!!\n",
                            "Platform : ", platform_name, "\n",
                            "Recipient : ", phone_number, "\n",
                            "Message : ", message_body
                        )
                        return "Message sent successfully via WhatsApp"
                    else:
                        raise ValueError("Unsupported platform")
                except Exception as e:
                    raise RuntimeError(f"Failed to send message: {str(e)}")

        def fetch_placeholders_for_recipients(phone_numbers, message_template, datasource):
            with Session() as session:
                try:
                    substitutions = {}
                    if not datasource:
                        return substitutions
                    for placeholder, config in datasource.items():
                        if config['type'] == 'database':
                            db_username = config['db_username']
                            db_password = config['db_password']
                            tablename = config['tablename']
                            tablecolumn = config['tablecolumn']
                            lookup_table = config['lookup_table']
                            lookup_col = config['lookup_col']
                            # Connect to the database
                            #db_uri = f"postgresql://{db_username}:{db_password}@localhost/mydatabase"
                            db_uri = "sqlite:///scheduling.db"
                            engine = create_engine(db_uri)
                            # Use a stored procedure or query to fetch data in batch
                            query = f"""
                                SELECT {lookup_table}.{lookup_col} AS phone_number, {tablecolumn} AS value
                                FROM {tablename}
                                JOIN {lookup_table} ON {tablename}.{lookup_col} = {lookup_table}.{lookup_col}
                                WHERE {lookup_table}.{lookup_col} IN :phone_numbers
                            """
                            results = engine.execute(query, phone_numbers=tuple(phone_numbers)).fetchall()
                            for row in results:
                                substitutions[row['phone_number']] = message_template.format(**{placeholder: row['value']})
                        elif config['type'] == 'excel':
                            # Process Excel data
                            excel_data = config.get('data', [])
                            print("config ", excel_data, phone_numbers)
                            for row in excel_data:
                                excel_phone_number = str(row.get('Phone'))
                                if excel_phone_number in phone_numbers:
                                    row['Phone'] = session.query(Contact.name).filter_by(phone=excel_phone_number).first()[0] # Safe to use [0] since tuple would be having only one elemnt which is name
                                    print("row ", row)
                                    substitutions[excel_phone_number] = message_template.format(**row)
                    return substitutions
                except Exception as fetch_exception:
                    raise fetch_exception


        def process_message(msg_id):
            print("Processing message")
            with Session() as session:
                try:
                    msg = session.query(ScheduledMessage).get(msg_id)
                    if not msg:
                        raise ValueError("Scheduled message not found")
                    if msg.recipient_type == 'group':
                        group_members = session.query(GroupMember).filter_by(group_id=msg.recipient_id).all()
                        contact = [session.query(Contact.phone).filter_by(id=member.contact_id).first()[0] for member in group_members]
                        print("Group contact ", contact)
                        #recipient_ids = [member.contact_id for member in group_members]
                        
                        # Fetch substitutions in batch (using stored procedure or callback)
                        substitutions = fetch_placeholders_for_recipients(
                            contact, msg.message_body, msg.datasource
                        )
                        max_failures_percentage = len(group_members)
                        actual_failures = 0
                        for member in group_members:
                            try:
                                phone_number = session.query(Contact.phone).filter_by(id=member.contact_id).first()[0]
                                substituted_message = substitutions.get(phone_number, msg.message_body)
                                response = send_message(
                                    msg.platform,
                                    member.contact_id,
                                    substituted_message,
                                )
                                msg = session.query(ScheduledMessage).get(msg_id)
                                msg.sent_time = datetime.utcnow()
                                log = PlatformLog(
                                    scheduled_message_id=msg.id,
                                    log_message='success',
                                    recipient_id=member.contact_id
                                )
                                session.add(log)
                                session.commit()
                                
                            except Exception as e:
                                log = PlatformLog(
                                    scheduled_message_id=msg.id,
                                    log_message=str(traceback.format_exc()),
                                    recipient_id=member.contact_id
                                )
                                session.add(log)
                                session.commit()
                                actual_failures += 1

                    elif msg.recipient_type == 'user':
                        contact = session.query(Contact.phone).filter_by(id=msg.recipient_id).first()[0] # [0] since the query result would be tuple
                        if not contact:
                            raise Exception("Unknown recipient id")
                        substitutions = fetch_placeholders_for_recipients(
                            [contact], msg.message_body, msg.datasource
                        )
                        substituted_message = substitutions.get(contact, msg.message_body)
                        response = send_message(
                            msg.platform,
                            msg.recipient_id,
                            substituted_message,
                        )
                        msg = session.query(ScheduledMessage).get(msg_id)
                        msg.status = 'sent'
                        msg.sent_time = datetime.utcnow()
                        log = PlatformLog(scheduled_message_id=msg.id, log_message=str(response), recipient_id=msg.recipient_id)
                        session.add(log)
                        session.commit()
                    # Reschedule if frequency is set
                    if msg.frequency:
                        print("Rescheduling message")
                        if msg.frequency == 'daily':
                            msg.scheduled_time += timedelta(days=1)
                        elif msg.frequency == 'weekly':
                            msg.scheduled_time += timedelta(weeks=1)
                        elif msg.frequency == 'monthly':
                            msg.scheduled_time += timedelta(days=30)
                        msg.status = 'scheduled'
                        session.commit()
        
                except Exception as e:
                    msg = session.query(ScheduledMessage).get(msg_id)
                    if msg:
                        msg.status = 'failed'
                        session.commit()
                    log = PlatformLog(scheduled_message_id=msg_id, log_message=str(traceback.format_exc()), recipient_id=msg.recipient_id)
                    session.add(log)
                    session.commit()

        def send_scheduled_messages():
            while True:
                try:
                    with Session() as session:
                        now = datetime.utcnow()
                        messages = session.query(ScheduledMessage).filter(
                            ScheduledMessage.scheduled_time <= now,
                            ScheduledMessage.status == 'scheduled'
                        ).all()
                        if not messages:
                            logging.info("No scheduled messages to process.")
                            time.sleep(10)  # Pause to reduce CPU usage if no messages are found
                            continue
                        logging.info(f"Found {len(messages)} messages to process.")
                        with ThreadPoolExecutor(max_workers=2) as executor:
                            for msg in messages:
                                msg.status = 'in-progress'
                                session.commit()
                                executor.submit(process_message, msg.id)
                except Exception as e:
                    logging.error(f"An error occurred while sending scheduled messages: {e}")
                    time.sleep(10)  # Sleep to avoid constant failure retries

        # Start the worker thread
        main_thread_2 = Thread(target=send_scheduled_messages, daemon=True)
        main_thread_2.start()
    return app

# Models
class PlatformLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    scheduled_message_id = db.Column(db.Integer, db.ForeignKey('scheduled_message.id', ondelete='CASCADE'), nullable=False)
    log_message = db.Column(db.String(200))

class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner_account.id', ondelete='CASCADE'), nullable=False)  # Link to OwnerAccount
    platform_name = db.Column(db.String(50), nullable=False)  # 'whatsapp', 'telegram', 'gmail'
    login_credentials = db.Column(db.Text, nullable=False)  # Encrypted credentials
    status = db.Column(db.String(20), default='active')  # Active/inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = db.relationship('OwnerAccount', back_populates='platforms')  # Relationship to OwnerAccount


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    owner_id = db.Column(
        db.Integer, 
        db.ForeignKey('owner_account.id', ondelete='CASCADE'),
        unique=True, 
        nullable=True
    )  # Break the cascading delete cycle by setting to NULL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    users = db.relationship('User', back_populates='organization')
    contacts = db.relationship('Contact', back_populates='organization')
    contact_groups = db.relationship('ContactGroup', back_populates='organization')
    group_members = db.relationship('GroupMember', back_populates='organization')


class OwnerAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )  # Allow user deletion to cascade
    organization_id = db.Column(
        db.Integer, 
        db.ForeignKey('organization.id', ondelete='CASCADE'),
        nullable=True
    )  # Prevent cascading deletes from causing a cycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    platforms = db.relationship('Platform', back_populates='owner', cascade='all, delete-orphan')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'employee'
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=True)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    contacts = db.relationship('Contact', back_populates='creator')
    contact_groups = db.relationship('ContactGroup', back_populates='creator')
    organization = db.relationship('Organization', back_populates='users')

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships for convenience
    creator = db.relationship('User', back_populates='contacts')
    organization = db.relationship('Organization', back_populates='contacts')
    groups = db.relationship('GroupMember', back_populates='contacts', cascade='all, delete-orphan')

    def __str__(self) -> str:
        return self.name


class ContactGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships for convenience
    creator = db.relationship('User', back_populates='contact_groups')
    organization = db.relationship('Organization', back_populates='contact_groups')
    members = db.relationship('GroupMember', back_populates='contact_groups', cascade='all, delete-orphan')


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('contact_group.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships for convenience
    contact_groups = db.relationship('ContactGroup', back_populates='members')
    contacts = db.relationship('Contact', back_populates='groups')
    organization = db.relationship('Organization', back_populates='group_members')


class ScheduledMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    recipient_type = db.Column(db.String(20), nullable=False)  # 'individual', 'group'
    recipient_id = db.Column(db.Integer, nullable=False)  # Contact ID or Group ID
    frequency = db.Column(db.Integer, default=0)  # Contact ID or Group ID
    message_body = db.Column(db.Text, nullable=False)
    platform = db.Column(
        db.Integer, 
        db.ForeignKey('platform.id', ondelete='CASCADE'),
        nullable=False
    )
    scheduled_time = db.Column(db.DateTime, nullable=False)
    datasource = db.Column(db.JSON, nullable=True)  # Store the entire datasource configuration
    excel_filename = db.Column(db.String, nullable=True)  # Store the unique filename of the Excel file
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'sent', 'canceled', 'failed'
    sent_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='unique_name_per_organization'),
    )
