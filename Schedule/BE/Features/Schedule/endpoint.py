import os
import uuid
import time
import json

import traceback

from datetime import datetime, timedelta
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine

from VendorApi.Whatsapp import SendException, WebHookException
from VendorApi.Whatsapp.message import TextMessage

import pyexcel
from flask import request, jsonify
from flask_cors import cross_origin
from database_schema import *

def init_endpoint(app_context, app, Session):
    with app_context:
        # Endpoints

        @app.route('/organization/<org_id>/robo', methods=['GET'])
        def get_robo_detail(org_id):
            with Session() as session:
                try:
                    robo_name = session.query(Organization).filter_by(id=org_id).first().robo_name
                    robo_user_id = session.query(User).filter_by(name=robo_name, organization_id=org_id).first().id
                    return jsonify({'id': robo_user_id, 'name': robo_name}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

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
        
        @app.route('/organization/name/<int:id>', methods=['GET'])
        @cross_origin()
        def get_organization_name(id):
            organization = Organization.query.get(id)
            if organization:
                return jsonify({
                    "name": organization.name,
                })
            return jsonify({"error": "Organization not found"}), 404

        @app.route('/organization/<int:id>', methods=['GET'])
        @cross_origin()
        def get_organization(id):
            organization = Organization.query.get(id)
            users = User.query.filter_by(organization_id=organization.id).all()
            users = [{"id": user.id, "name": user.name, "phone": user.phone} for user in users]
            if organization:
                return jsonify({
                    "id": organization.id,
                    "name": organization.name,
                    "owner_id": organization.owner_id,
                    "employees": users
                })
            return jsonify({"error": "Organization not found"}), 404
        
        @app.route('/organization', methods=['GET'])
        @cross_origin()
        def get_organizations():
            organizations = Organization.query.all()
            return jsonify([{
                "name": organization.name
            } for organization in organizations])

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
                "login_id": p.login_id,
                "token": p.login_credentials,
                "status": p.status,
            } for p in platforms]), 200
        
        @app.route('/platforms', methods=['POST'])
        @cross_origin()
        def add_platform():
            data = request.json
            if not data.get('platform_name'):
                return jsonify({"error": "Platform is required"}), 400
            if not data.get('owner_id'):
                return jsonify({"error": "Owner ID is required"}), 400
            platform = Platform.query.filter_by(owner_id=data['owner_id'], platform_name=data['platform_name']).first()
            if platform:
                return jsonify({"error": "Platform already added to the organization"}), 409
            with Session() as session:
                platform = Platform(
                    owner_id=data['owner_id'],
                    platform_name=data['platform_name'],
                    login_id=data['login_id'],
                    login_credentials=data['token']
                )
                session.add(platform)
                session.commit()
                return jsonify({"message": "Platform added successfully!"}), 201

        @app.route('/platforms', methods=['PUT'])
        @cross_origin()
        def update_platform():
            print("Updating Platform")
            data = request.json
            if not data.get('id'):
                return jsonify({'error': 'Platform Id is required'}), 404
            if not data.get('owner_id'):
                return jsonify({'error': 'Please login to edit the platform'}), 403
            with Session() as session:
                platform = session.query(Platform).filter_by(id=data['id']).first()
                if platform.owner_id != data['owner_id']:
                    return jsonify({'error': 'Sorry! - You dont have permission'}), 403
                if not platform:
                    return jsonify({"error": "Platform not found"}), 404
                platform.login_id = data['login_id']
                platform.login_credentials = data['token']
                print("Platform token ", data['token'])
                session.commit()
                return jsonify({"message": "Platform updated successfully!"}), 200

        @app.route('/platforms', methods=['DELETE'])
        @cross_origin()
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
                    if user:
                        _uuid = session.query(Uuid).filter_by(organization_id=user.organization_id, uuid=data['uuid']).first()
                        if _uuid:
                            return jsonify({"error": "Systems already registered in the organization"})
                    with session.begin_nested():
                        user = User(
                            name=data['name'],
                            phone=data['phone'],
                            email=data['email'],
                            user_type=data['user_type'],
                            password=data['password'],  # Hash in production
                            uuid=data['uuid']
                        )
                        session.add(user)
                        session.flush()
                        organization = session.query(Organization).filter_by(name=data['organization']).first()
                        if data['user_type'] == 'owner':
                            if not organization:
                                organization = Organization(
                                    name=data['organization'],
                                    owner_id=user.id,
                                    robo_name=data['robo_name']
                                )
                                session.add(organization)
                                session.flush()
                            user.organization_id = organization.id
                            session.add(user)

                            # Create robo user
                            robo_user = User(
                                name=data['robo_name'],
                                phone='000000000',
                                email='robo@solvedesktop.com',
                                user_type='employee',
                                password='10011001',  # Hash in production
                                uuid='012210'
                            )
                            session.add(robo_user)

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
                                    login_id=data['login_id'],
                                    login_credentials=data['platform_login_credentials']
                                )
                                session.add(platform)
                            session.flush()
                        elif data['user_type'] == 'employee':
                            user.organization_id = organization.id
                            session.add(user)
                        _uuid = Uuid(
                            organization_id=user.organization_id,
                            uuid=data['uuid']
                        )
                        session.add(_uuid)
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
            uuid = data.get("uuid")
            if not uuid:
                return jsonify({"error": "UUID is required"}), 400
            with Session() as session:
                user = session.query(User).filter_by(phone=data['phone']).first()
                _uuid = session.query(Uuid).filter_by(organization_id=user.organization_id, uuid=uuid).first()
                if not _uuid:
                    return jsonify({"error": "No such systems registered in the organization"}), 401
                if user and user.password == data['password']:  # Verify hash in production
                    if user.uuid != uuid:
                        already_assigned_mac_address = User.query.filter_by(uuid=uuid).first()
                        already_assigned_mac_address.uuid = None
                        # Update the uuid since the user seems to changed(motherboard replaced) the system
                        user.uuid = uuid
                        session.commit()
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
            print(file, "exists ", os.path.exists(file)) 
            sheet = pyexcel.get_sheet(file_name=file)
            data = []
            headers = sheet.row[0]  # First row as headers
            for row in sheet.row[1:]:
                data.append(dict(zip(headers, row)))
            return data

        def dump_for_excel_datasource(datasource):
            print("datasource ", datasource)
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
            frequency = request.form.get('frequency')
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
                        frequency=frequency,
                        organization_id=organization_id,
                        datasource=datasource,  # Store the entire datasource configuration
                        excel_filename=",".join(excel_filenames),  # Store filenames as comma-separated string
                        scheduled_time=datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                    )
                    session.add(message)
                    session.commit()
                    return jsonify({"message": "Message scheduled successfully!"}), 201
                except Exception as e:
                    app.logger.info(str(traceback.format_exc()))
                    return jsonify({"error": str(e)}), 400
          except Exception as ex:
            app.logger.info(str(traceback.format_exc()))

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
                            "scheduled_time": schedule.scheduled_time.isoformat(),
                            "frequency": schedule.frequency,
                            "message_body": schedule.message_body,
                            "status": schedule.status
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
                            app.logger.error(str(file_remove_exception))
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
        @cross_origin()
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
        @cross_origin()
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
            name = data.get('name')
            description = data.get('description')
            image = data.get('image')
            address = data.get('address')
            category = data.get('category')
            phone = data.get('phone')
            created_by=data.get('created_by')
            organization_id=data.get('organization_id')
            contact = Contact.query.filter_by(phone=phone, organization_id=organization_id).first()
            if contact:
                return jsonify({"error": "Contact is already existing"}), 409
            with Session() as session:
                try:
                    contact = Contact(
                        name=name,
                        phone=phone,
                        created_by=created_by,
                        organization_id=organization_id,
                        description=description,
                        image=image,
                        address=address,
                        category=category
                    )
                    session.add(contact)
                    session.commit()
                    contact_id = contact.id
                    return jsonify({"id": contact_id}), 201
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
        
        @app.route('/contacts/import', methods=['POST'])
        @cross_origin()
        def upload_contacts():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({'error': 'Organization ID is required'}), 400
            created_by = request.args.get('created_by')
            if not created_by:
                return jsonify({'error': 'Created by is required'}), 400

            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
        
            file = request.files['file']
        
            try:
                # Read the uploaded file into pyexcel's Sheet
                sheet = pyexcel.get_sheet(file_type='xlsx', file_content=file.read())
        
                # Validate required fields
                required_columns = ['name', 'description', 'phone', 'address', 'category']
                sheet_columns = sheet.row_at(0)  # Assuming first row is the header
                if not all(col in sheet_columns for col in required_columns):
                    return jsonify({'error': 'Invalid file format'}), 400
        
                # Process the data and store it (mock logic)
                imported_count = 0
                
                with Session() as session:
                    try:
                        for row in sheet.rows():
                            if row == sheet_columns:  # Skip the header row
                                continue
                            contact_data = dict(zip(sheet_columns, row))
                            print("contact_data ", contact_data)
                            contact = session.query(Contact).filter_by(phone=contact_data['phone'], organization_id=organization_id).first()
                            if contact:
                                continue
                            contact = Contact(
                                name=contact_data.get('name'),
                                phone=contact_data.get('phone'),
                                description=contact_data.get('description'),
                                image=contact_data.get('image'),
                                address=contact_data.get('address'),
                                category=contact_data.get('category'),
                                created_by=created_by,
                                organization_id=organization_id
                            )
                            print(f"Importing contact: {contact_data}")
                            session.add(contact)
                            session.commit()
                            imported_count += 1
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500
                return jsonify({'message': 'Contacts imported successfully', 'importedCount': imported_count}), 200

            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/contacts', methods=['GET'])
        @cross_origin()
        def get_contacts():
            # Get the query parameters
            organization_id = request.args.get('organization_id')
            page = request.args.get('page', type=int)
            # TODO: Handle paging from UI since 10k is very expensive
            per_page = request.args.get('per_page', type=int, default=10000)
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
            result = [
                {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "description": c.description,
                "image": c.image,
                "address": c.address,
                "category": c.category,
                "organization_id": c.organization_id,
                "created_by": c.created_by
                }
                for c in contacts
            ]
            return jsonify(result), 200
        
        @app.route('/contacts/<int:organization_id>', methods=['GET'])
        def get_contact_id_from_phone(organization_id):
            # Get the query parameters for the phone number
            result = Contact.query.filter_by(phone=request.args.get('phone'), organization_id=organization_id).first()
            return jsonify({"id": result.id, "name": result.name, "phone": result.phone, "created_by": result.created_by})

        @app.route('/contacts', methods=['PUT'])
        @cross_origin()
        def edit_contact():
            data = request.json
            contact_id = data.get('id')
            print("contact id ", contact_id)
            if not contact_id:
                return jsonify({"error": "Contact ID is required"}), 400
            try:
                with Session() as session:
                    # Query the contact within the session context
                    contact = session.query(Contact).get(contact_id)
                    if not contact:
                        return jsonify({"error": "Contact not found"}), 404
                    # Update fields
                    contact.name = data.get('name', contact.name)
                    contact.phone = data.get('phone', contact.phone)
                    contact.description = data.get('description', contact.description)
                    contact.image = data.get('image', contact.image)
                    contact.address = data.get('address', contact.address)
                    contact.category = data.get('category', contact.category)
                    # Commit the changes
                    session.commit()
                return jsonify({"message": "Contact updated successfully!"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400


        @app.route('/contacts/<int:contact_id>', methods=['DELETE', 'OPTIONS'])
        @cross_origin(origins="http://localhost:4200")
        def delete_contact(contact_id):
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
            organization_id = data.get('organization_id')
            created_by = data.get('created_by')
            name = data.get('name')
            description=data.get('description')
            category=data.get('category')
            if not organization_id:
                return jsonify({"error": "Organization Id is required"}), 400
            if not created_by:
                return jsonify({"error": "Creator Id is required"}), 400
            if not name:
                return jsonify({"error": "Group Name is required"}), 400
            group = ContactGroup.query.filter_by(name=name, organization_id=organization_id).first()
            if group:
                return jsonify({"error": "Group with this name already existing"}), 409
            with Session() as session:
                try:
        		    # TODO: Confirm if the group is already existing
                    group = ContactGroup(
                        name=name,
                        organization_id=organization_id,
                        created_by=created_by,
                        description=description,
                        category=category
                    )
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
            group_id = request.args.get('group_id')
            page = request.args.get('page', type=int)
            # TODO: Handle paging from UI since 10k is very expensive
            per_page = request.args.get('per_page', type=int, default=10000)
            if not organization_id:
                return jsonify({"error" : "Organization ID is required"}), 400
            with Session() as session:
                # Filter the contacts by organization_id
                query = session.query(ContactGroup).filter_by(organization_id=organization_id)
                if group_id:
                    query = query.filter_by(id=group_id)
                # Check if pagination is needed
                if page:
                    groups = query.paginate(page=page, per_page=per_page).items
                else:
                    groups = query.all()  # Fetch all results if no pagination
                # Format the results
                response = []
                for g in groups:
                    temp = {
                        "id": g.id,
                        "name": g.name,
                        "organization_id": g.organization_id,
                        "description": g.description,
                        "category": g.category,
                        "created_by": g.created_by,
                    }
                    members = session.query(GroupMember).filter_by(group_id=g.id, organization_id=organization_id).all()
                    memebers_list = []
                    for member in members:
                        contact = session.query(Contact).filter_by(id=member.contact_id).first()
                        memebers_list.append(
                            {
                            "id": member.id,
                            "group_id": member.group_id,
                            "organization_id": member.organization_id,
                            "created_at": member.created_at.isoformat(),
                            "contact_id": contact.id,
                            "contact_name": contact.name,
                            "contact_phone": contact.phone
                            }
                        )
                    temp.update({"members": memebers_list})
                    temp.update({"total": len(memebers_list)})
                    response.append(temp)
                return jsonify(response), 200

        @app.route('/groups', methods=['PATCH'])
        @cross_origin()
        def patch_groups():
            data = request.json
            # Get the query parameters
            organization_id = data.get('organization_id')
            group_id = data.get('id')
            if not organization_id:
                return jsonify({"error" : "Organization ID is required"}), 400
            if not group_id:
                return jsonify({"error": "Group ID is required"}), 400
            with Session() as session:
                # Filter the contacts by organization_id
                exiting_group_snapshot = session.query(ContactGroup).filter_by(id=group_id, organization_id=organization_id).first()
                exiting_group_snapshot.name = data.get('name', exiting_group_snapshot.name)
                exiting_group_snapshot.description = data.get('description', exiting_group_snapshot.description)
                exiting_group_snapshot.category = data.get('category', exiting_group_snapshot.category)
                session.commit()
                members = session.query(GroupMember).filter_by(group_id=group_id, organization_id=organization_id).all()
                existing_members_snapshot = {member.id for member in members}
                new_members_snapshot = {member.get('id') if isinstance(member, dict) else member.id for member in data.get('members', members)}
                members_to_be_removed = existing_members_snapshot - new_members_snapshot
                for member_to_be_removed in members_to_be_removed:
                    group_member = session.query(GroupMember).filter_by(id=member_to_be_removed).first()
                    session.delete(group_member)
                    session.commit()
                return jsonify({"message": "Group patch successfull!"}), 200

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
                app.logger.info("Data %s", data)
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
                        return jsonify({"member_id": existing_member.id}), 201
                    # Add the contact to the group
                    group_member = GroupMember(
                        group_id=group_id, organization_id=organization_id, contact_id=contact_id
                    )
                    session.add(group_member)
                    session.commit()
                    return jsonify({"member_id": group_member.id}), 201
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

        @app.route('/schedule/history', methods=["GET"])
        @cross_origin()
        def get_schedule_message_history():
            history = []
            organization_id = request.args.get("organization_id")
            if not organization_id:
                return jsonify({"error": "Organization ID is required"}), 400
            with Session() as session:
                try:
                    messages = session.query(PlatformLog).filter_by(organization_id=int(organization_id)).all()
                    if messages:
                        schedule_detail = session.query(ScheduledMessage).filter_by(id=messages[0].scheduled_message_id).first()
                        temp_schedule_id = schedule_detail.id
                        for message in messages:
                            if message.scheduled_message_id != temp_schedule_id:
                                temp_schedule_id = message.scheduled_message_id
                                schedule_detail = session.query(ScheduledMessage).filter_by(id=message.scheduled_message_id).first()
                            send_date = schedule_detail.sent_time
                            schedule_name = schedule_detail.name
                            user_name = session.query(Contact).filter_by(id=message.recipient_id).first().name
                            history.append({
                                "id": message.id,
                                "schedule_name": schedule_name,
                                "recipient": user_name,
                                "send_date": send_date,
                                "status": message.status,
                                "status_details": message.log_message
                            })

                    return jsonify(history), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

        @app.route('/schedule/ping', methods=["GET"])
        def ping_schedule_service():
            return jsonify({"message": "Schedule service is alive"}), 200

        # Placeholder for platform-specific message sending
        def send_message(platform_id, recipient_id, message_body):
            with Session() as session:
                try:
                    platform = session.query(Platform).filter_by(id=platform_id).first()
                    platform_name = platform.platform_name
                    phone_number_id = platform.login_id
                    token = platform.login_credentials
                    recipient_phone_number = session.query(Contact.phone).filter_by(id=recipient_id).first()[0]
                    #TODO: Fetch credetials for the specific platform as well
                    if platform_name.startswith('whatsapp'):
                        # Add WhatsApp API integration logic here
                        print(
                            "Message Sent!!\n",
                            "Platform : ", platform_name, "\n",
                            "Login Id : ", phone_number_id, "\n", 
                            "From Key : ", token, "\n",
                            "Recipient : ", recipient_phone_number, "\n",
                            "Message : ", message_body, "\n"
                        )
                        # Send WhatsApp message
                        if phone_number_id:
                            text_message = TextMessage(
                                phone_number_id=phone_number_id,
                                token=token
                            )
                            response = text_message.send_message(recipient_phone_number, message_body)
                            response = response.json()
                            return response
                    else:
                        raise ValueError("Unsupported platform")
                except WebHookException as webhook_error:
                    raise RuntimeError(f"Webhook error - failed to read notification: {str(webhook_error)}")
                except SendException as send_error:
                    raise RuntimeError(f"Whatsapp error - failed to send message: {str(send_error)}")
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


        def process_message(msg, session):
                print("Processing message")
                try:
                    #msg = session.query(ScheduledMessage).get(msg_id)
                    if not msg:
                        raise ValueError("Scheduled message not found")
                    org_id = msg.organization_id
                    if msg.recipient_type == 'group':
                        group_members = session.query(GroupMember).filter_by(group_id=msg.recipient_id).all()
                        contact = [session.query(Contact.phone).filter_by(id=member.contact_id).first()[0] for member in group_members]
                        print("Group contact ", contact)
                        #recipient_ids = [member.contact_id for member in group_members]
                        
                        # Fetch substitutions in batch (using stored procedure or callback)
                        substitutions = fetch_placeholders_for_recipients(
                            contact, msg.message_body, msg.datasource
                        )
                        max_failures = len(group_members)
                        actual_failures = 0
                        actual_failure_reason = {}
                        for member in group_members:
                            user_message = None
                            try:
                                phone_number = session.query(Contact.phone).filter_by(id=member.contact_id).first()[0]
                                substituted_message = substitutions.get(phone_number, msg.message_body)
                                robo_name = session.query(Organization).filter_by(id=org_id).first().robo_name
                                robo_user_id = session.query(User).filter_by(name=robo_name, organization_id=org_id).first().id
                                conversation = Conversation(
                                    assigned_user_id=robo_user_id,
                                    organization_id=org_id,
                                    platform_id=msg.platform,
                                    contact_id=member.contact_id,
                                    open_by=robo_name,
                                    closed_by=robo_user_id,
                                    status='closed'
                                )
                                session.add(conversation)
                                session.flush()
                                user_message = UserMessage(
                                    conversation_id=conversation.id,
                                    organization_id=conversation.organization_id,
                                    platform_id=conversation.platform_id,
                                    user_id=robo_user_id,
                                    message_body=substituted_message,
                                    status="failed",
                                    messageid=None,
                                )
                                session.add(user_message)
                                session.commit()
                                response = send_message(
                                    msg.platform,
                                    member.contact_id,
                                    substituted_message,
                                )
                                msg_id = response['messages'][0].get('id')
                                user_message.messageid = msg_id
                                user_message.status = "sent_to_server"
                                #msg = session.query(ScheduledMessage).get(msg_id)
                                msg.sent_time = datetime.utcnow()
                                platform_log_msg = json.dumps({phone_number: {"messageid": msg_id, "Error": None}})
                                log = PlatformLog(
                                    scheduled_message_id=msg.id,
                                    log_message=platform_log_msg,
                                    recipient_id=member.contact_id,
                                    organization_id=org_id,
                                    messageid=msg_id,
                                    status="Ok"
                                )
                                session.add(log)
                                session.commit()
                                
                            except Exception as group_member_exc:
                                exc_message=str(traceback.format_exc())
                                platform_log_msg = json.dumps({phone_number: {"messageid": None, "Error": exc_message}})
                                log = PlatformLog(
                                    scheduled_message_id=msg.id,
                                    log_message=platform_log_msg,
                                    recipient_id=member.contact_id,
                                    organization_id=org_id,
                                    status="Error"
                                )
                                session.add(log)
                                user_message.status_details = str(group_member_exc)
                                session.commit()
                                actual_failure_reason.update({phone_number: exc_message})
                                actual_failures += 1
                        if actual_failures == 0:
                            msg.status = "sent"
                        elif actual_failures < max_failures:
                            msg.status = "partially_failed"
                            msg.msg_status = json.dumps(actual_failure_reason)
                        else:
                            msg.status = "failed"
                            msg.msg_status = json.dumps(actual_failure_reason)
                        session.commit()

                    elif msg.recipient_type == 'user':
                        contact = session.query(Contact.phone).filter_by(id=msg.recipient_id).first()[0] # [0] since the query result would be tuple
                        if not contact:
                            raise Exception("Unknown recipient id")
                        substitutions = fetch_placeholders_for_recipients(
                            [contact], msg.message_body, msg.datasource
                        )
                        substituted_message = substitutions.get(contact, None)#msg.message_body)
                        robo_name = session.query(Organization).filter_by(id=org_id).first().robo_name
                        robo_user_id = session.query(User).filter_by(name=robo_name, organization_id=org_id).first().id
                        conversation = Conversation(
                            assigned_user_id=robo_user_id,
                            organization_id=org_id,
                            platform_id=msg.platform,
                            contact_id=msg.recipient_id,
                            open_by=robo_name,
                            closed_by=robo_user_id,
                            status='closed'
                        )
                        session.add(conversation)
                        session.flush()
                        user_message = UserMessage(
                            conversation_id=conversation.id,
                            organization_id=conversation.organization_id,
                            platform_id=conversation.platform_id,
                            user_id=robo_user_id,
                            message_body=substituted_message,
                            status="failed",
                            messageid=None
                        )
                        session.add(user_message)
                        session.commit()
                        if not substituted_message:
                            #msg = session.query(ScheduledMessage).get(msg_id)
                            msg.status = 'failed'
                            msg.msg_status = 'failed'
                            session.flush()
                            exc_message = "Missing format for the contact"
                            platform_log_msg = json.dumps({contact: {"messageid": None, "Error": exc_message}})
                            log = PlatformLog(
                                scheduled_message_id=msg.id,
                                log_message=platform_log_msg,
                                recipient_id=msg.recipient_id,
                                organization_id=org_id,
                                status="Error"
                            )
                            session.add(log)
                            user_message.status_details = exc_message
                            session.commit()
                            return
                        response = None
                        try:
                            response = send_message(
                                msg.platform,
                                msg.recipient_id,
                                substituted_message,
                            )
                        except Exception as user_msg_e:
                            user_message.status_details = str(user_msg_e)
                            session.commit()
                            raise Exception from user_message

                        #msg = session.query(ScheduledMessage).get(msg_id)
                        msg_id = response['messages'][0].get('id')
                        user_message.messageid = msg_id
                        user_message.status = "sent_to_server"
                        msg.messageid = response['messages'][0].get('id')
                        msg.status = 'sent'
                        msg.msg_status = 'sent_to_server'
                        msg.sent_time = datetime.utcnow()
                        session.flush()
                        platform_log_msg = json.dumps({contact: {"messageid": msg_id, "Error": None}})
                        log = PlatformLog(
                            scheduled_message_id=msg.id,
                            log_message=platform_log_msg,
                            recipient_id=msg.recipient_id,
                            organization_id=org_id,
                            status="Ok",
                            messageid=msg_id
                        )
                        session.add(log)
                        session.commit()
                    # Reschedule if frequency is set
                    if msg.frequency >= 0:
                        print("Rescheduled message")
                        current_time = datetime.utcnow()
                        if msg.frequency == 0:  # Daily
                            msg.scheduled_time = current_time + timedelta(days=1)
                            #msg.scheduled_time = current_time + timedelta(minutes=1)
                        elif msg.frequency == 1:  # Weekly
                            msg.scheduled_time = current_time + timedelta(weeks=1)
                        elif msg.frequency == 2:  # Monthly
                            msg.scheduled_time = current_time + timedelta(days=30)  # Approximation for 1 month
                        elif msg.frequency == 3:  # Quarterly
                            msg.scheduled_time = current_time + timedelta(days=91)  # Approximation for 3 months
                        elif msg.frequency == 4:  # Half-Yearly
                            msg.scheduled_time = current_time + timedelta(days=182)  # Approximation for 6 months
                        elif msg.frequency == 5:  # Yearly
                            msg.scheduled_time = current_time + timedelta(days=365)  # Approximation for 1 year
                        #if msg.frequency == 'daily':
                        #    msg.scheduled_time += timedelta(days=1)
                        #elif msg.frequency == 'weekly':
                        #    msg.scheduled_time += timedelta(weeks=1)
                        #elif msg.frequency == 'monthly':
                        #    msg.scheduled_time += timedelta(days=30)
                        #msg = session.query(ScheduledMessage).get(msg_id)
                        msg.status = 'scheduled'
                        session.commit()
        
                except Exception as e:
                    #msg = session.query(ScheduledMessage).get(msg_id)
                    if msg:
                        msg.status = 'failed'
                        msg.msg_status = 'failed'
                        session.commit()
                    exc_message = str(traceback.format_exc())
                    platform_log_msg = json.dumps({contact: {"messageid": None, "Error": exc_message}})
                    log = PlatformLog(
                        scheduled_message_id=msg.id,
                        log_message=platform_log_msg,
                        recipient_id=msg.recipient_id,
                        organization_id=org_id,
                        status="Error"
                    )
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
                            app.logger.info("No scheduled messages to process.")
                            time.sleep(10)  # Pause to reduce CPU usage if no messages are found
                            continue
                        app.logger.info(f"Found {len(messages)} messages to process.")
                        #with ThreadPoolExecutor(max_workers=1) as executor:
                        for msg in messages:
                            msg.status = 'in-progress'
                            session.commit()
                            #executor.submit(process_message, msg, session)
                            process_message(msg, session)
                    print("session exited")
                except Exception as e:
                    app.logger.error(f"An error occurred while sending scheduled messages: {e}")
                    time.sleep(10)  # Sleep to avoid constant failure retries

        def close_old_conversations():
            # Get 24 hours ago from current time
            time_threshold = datetime.utcnow() - timedelta(hours=24)
            while True:
                try:
                    with Session() as session:
                        # Update all conversations that are older than 24 hours and are still open
                        conversations_to_be_closed = session.query(Conversation).filter(
                            Conversation.created_at < time_threshold,
                            Conversation.status != "closed"
                        ).all()
                        if not conversations_to_be_closed:
                            app.logger.info("No conversations surpassed 24 hour window")
                            time.sleep(300) # To avoid unnecessary holding of CPU cycles.
                            continue
                        for conversation_to_be_closed in conversations_to_be_closed:
                            org_id = conversation_to_be_closed.organization_id
                            robo_name = session.query(Organization).filter_by(id=org_id).first().robo_name
                            robo_id = session.query(User).filter_by(name=robo_name, organization_id=org_id).first().id
                            conversation_to_be_closed.status = "closed"
                            conversation_to_be_closed.closed_reason = "conversation surpassed 24 hours window"
                            conversation_to_be_closed.closed_by = robo_id
                            session.commit()
                except Exception as e:
                    app.logger.error(f"An error occurred while cleaning up conversation: {e}")
                    time.sleep(60)  # Sleep to avoid constant failure retries
                
        
        # Start the worker thread
        main_thread_2 = Thread(target=send_scheduled_messages, daemon=True)
        main_thread_2.start()

        main_thread_3 = Thread(target=close_old_conversations, daemon=True)
        main_thread_3.start()

