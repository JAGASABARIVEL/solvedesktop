import os
from threading import Thread
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_cors import cross_origin
from sqlalchemy import or_, func, case
import traceback

from database_schema import IncomingMessage, MessageResponseLog, Conversation, User, UserMessage, Contact, Platform

from Features.Messages import ConsumerService

from VendorApi.Whatsapp import SendException, WebHookException
from VendorApi.Whatsapp.message import TextMessage

REG_APP_NAME = "conversation"

TOPIC = "whatsapp"
GRP_ID = "whatsapp-grp"
BOOTSTRAP_SERVER = "localhost:9092"

def read_config():
  # reads the client configuration from client.properties
  # and returns it as a key-value map
  config = {}
  with open("kafka.config") as fh:
    for line in fh:
      line = line.strip()
      if len(line) != 0 and line[0] != "#":
        parameter, value = line.strip().split('=', 1)
        config[parameter] = value.strip()
  return config

def init_endpoint(app_context, app, Session):
    with app_context:
        def start_consumer():
            # TODO: Remove the hardcoded credentials of kafka
            kafka_config = read_config()
            #kafka_config["sasl.username"] = os.getenv("kf_username")
            #kafka_config["sasl.password"] = os.getenv("kf_password")
            print("kafka_config ", kafka_config)
            ConsumerService(app, topic=TOPIC, group_id=GRP_ID, config=kafka_config, session=Session).run()
        # Start the consumer in a separate thread
        consumer_thread = Thread(target=start_consumer, daemon=True)
        consumer_thread.start()

        # Endpoints
        @app.route('/chat/ping', methods=['GET'])
        @cross_origin()
        def ping_message_service():
            return jsonify({"message": "Message service is alive"}), 200
        
        
        @app.route('/chat/conversations', methods=['GET'])
        @cross_origin()
        def get_unassigned_conversations():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({'error': 'Organization ID is required'}), 400
            conversation_status = request.args.get('conversation_status')
            contact_id = request.args.get('contact_id')
            assignee = request.args.get('assignee')
            with Session() as session:
                conversations = session.query(Conversation).filter_by(organization_id=organization_id)
                if conversation_status:
                    conversation_statuses = conversation_status.split(',')
                    conversations = conversations.filter(
                        or_(*[Conversation.status == status for status in conversation_statuses])
                    )
                if contact_id:
                    conversations = conversations.filter_by(contact_id=contact_id)
                if assignee:
                    conversations = conversations.filter_by(assigned_user_id=assignee)
                if not conversations:
                    return jsonify([])
                result = []
                for conv in conversations:
                    incoming_msgs = session.query(IncomingMessage).filter_by(conversation_id=conv.id).all()
                    incoming_messages = [
                        {
                            'id': msg.id,
                            'type': 'customer',
                            'message_body': msg.message_body,
                            'status': msg.status,
                            'status_details': msg.status_details,
                            'received_time': msg.received_time
                        }
                        for msg in incoming_msgs
                    ]
                    # Fetch assigned user messages (if any table exists for user messages, example UserMessage)
                    user_msgs = session.query(UserMessage).filter_by(conversation_id=conv.id).all()
                    assigned_user_messages = [
                        {
                            'id': msg.id,
                            'type': 'org',
                            'message_body': msg.message_body,
                            'status': msg.status,
                            'status_details': msg.status_details,
                            'sent_time': msg.sent_time,
                            'sender': msg.user_id
                        }
                        for msg in user_msgs
                    ]
                    # Combine both incoming and assigned user messages and sort them by time
                    combined_messages = incoming_messages + assigned_user_messages
                    combined_messages.sort(key=lambda x: x['received_time'] if x['type'] == 'customer' else x['sent_time'])
                    assigned_user = session.query(User).get(conv.assigned_user_id)
                    contact = session.query(Contact).get(conv.contact_id)
                    if not assigned_user:
                        conv_data = {
                            'conversation_id': conv.id,
                            'contact': {
                                'id': contact.id,
                                'name': contact.name,
                                'phone': contact.phone
                            },
                            'assigned': None,
                            'organization_id': conv.organization_id,
                            'status': conv.status,
                            'created_at': conv.created_at,
                            'messages': combined_messages,
                            'open_by': conv.open_by,
                            'closed_by': conv.closed_by,
                            'closed_reason': conv.closed_reason
                        }
                    else:
                        conv_data = {
                            'conversation_id': conv.id,
                            'contact': {
                                'id': contact.id,
                                'name': contact.name,
                                'phone': contact.phone
                            },
                            'assigned': {
                                'id': assigned_user.id,
                                'name': assigned_user.name
                            },
                            'organization_id': conv.organization_id,
                            'status': conv.status,
                            'created_at': conv.created_at,
                            'messages': combined_messages,
                            'open_by': conv.open_by,
                            'closed_by': conv.closed_by,
                            'closed_reason': conv.closed_reason
                        }
                    result.append(conv_data)
                return jsonify(result)
        
        @app.route('/chat/conversations/<int:conversation_id>', methods=['GET'])
        @cross_origin()
        def get_conversation(conversation_id):
            with Session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id)
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                assignee_filter = request.args.get('assignee')
                if assignee_filter:
                    conversation = conversation.filter_by(assigned_user_id=assignee_filter)
                if not conversation:
                    return jsonify({'success': 'No conversation found for the user'}), 200
                # It safe to to first() since we should only 1 conversation record
                conversation = conversation.first()
                incoming_msgs = session.query(IncomingMessage).filter_by(conversation_id=conversation_id).all()
                contact = session.query(Contact).get(conversation.contact_id)
                assignee = None
                if conversation.assigned_user_id:
                    assignee = session.query(User).get(conversation.assigned_user_id)
                incoming_messages = [
                    {
                        'id': msg.id,
                        'type': 'customer',
                        'message_body': msg.message_body,
                        'status': msg.status,
                        'status_details': msg.status_details,
                        'received_time': msg.received_time
                    }
                    for msg in incoming_msgs
                ]
                # Fetch assigned user messages (if any table exists for user messages, example UserMessage)
                user_msgs = session.query(UserMessage).filter_by(conversation_id=conversation_id).all()
                assigned_user_messages = [
                    {
                        'id': msg.id,
                        'type': 'org',
                        'message_body': msg.message_body,
                        'status': msg.status,
                        'status_details': msg.status_details,
                        'sent_time': msg.sent_time,
                        'sender': msg.user_id
                    }
                    for msg in user_msgs
                ]
                # Combine both incoming and assigned user messages and sort them by time
                combined_messages = incoming_messages + assigned_user_messages
                combined_messages.sort(key=lambda x: x['received_time'] if x['type'] == 'customer' else x['sent_time'])
                return jsonify({
                    'conversation_id': conversation.id,
                    'contact': {
                        'id': contact.id,
                        'name': contact.name,
                        'phone': contact.phone
                    },
                    'assigned': {
                        'id': assignee.id if assignee else None,
                        'name': assignee.name if assignee else None
                    },
                    'created_at': conversation.created_at,
                    'organization_id': conversation.organization_id,
                    'status': conversation.status,
                    'messages': combined_messages
                })
        
        @app.route('/chat/conversations/assign/<int:conversation_id>', methods=['POST'])
        @cross_origin()
        def assign_conversation(conversation_id):
            with Session() as session:
                data = request.get_json()
                user_id = data.get('id')
                conversation = session.query(Conversation).get(conversation_id)
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                user = session.query(User).get(user_id)
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                conversation.assigned_user_id = user_id
                conversation.status = 'active'
                conversation.updated_at = datetime.utcnow()
                session.commit()
                return jsonify({'message': 'Conversation assigned successfully', 'conversation_id': conversation.id, 'assigned_user_id': user_id})

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
                                token=token,
                                client_application=REG_APP_NAME
                            )
                            response = text_message.send_message(recipient_phone_number, message_body)
                            print("sent message to whatsapp ", response.content)
                            return response
                    else:
                        raise ValueError("Unsupported platform")
                except WebHookException as webhook_error:
                    raise RuntimeError(f"Webhook error - failed to read notification: {str(webhook_error)}")
                except SendException as send_error:
                    raise RuntimeError(f"Whatsapp error - failed to send message: {str(send_error)}")
                except Exception as e:
                    raise RuntimeError(f"Failed to send message: {str(e)}")

        @app.route('/chat/conversations/respond', methods=['POST'])
        @cross_origin()
        def respond_to_message():
            data = request.json
            conversation_id = data.get('conversation_id')
            message_body = data.get('message_body')
            user_id = data.get('user_id')
            # TODO: Update the status after checking the webhook notification
            status = "sent_to_server"
            response = None
            with Session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                # Incase conversation closed already
                conversation.status = 'active'
                session.commit()
                try:
                    response = send_message(
                        platform_id=conversation.platform_id,
                        recipient_id=conversation.contact_id,
                        message_body=message_body
                    )
                    response = response.json()
                except Exception as send_ex:
                    user_message = UserMessage(
                        conversation_id=conversation.id,
                        organization_id=conversation.organization_id,
                        platform_id=conversation.platform_id,
                        user_id=user_id,
                        message_body=message_body,
                        status='failed',
                        status_details = str(send_ex),
                        messageid="Cannot send"
                    )
                    session.add(user_message)
                    session.commit()
                    print(send_ex)
                    return jsonify({'status': 'error', 'message': 'Conversation - Could not deliver the message'}), 500
                user_message = UserMessage(
                    conversation_id=conversation.id,
                    organization_id=conversation.organization_id,
                    platform_id=conversation.platform_id,
                    user_id=user_id,
                    message_body=message_body,
                    status=status,
                    messageid=response['messages'][0].get('id')
                )
                session.add(user_message)
                session.commit()
                return jsonify({'status': 'success', 'message': 'Response logged successfully'}), 200
        
        @app.route('/chat/conversations/close/<int:conversation_id>', methods=['POST'])
        @cross_origin()
        def close_conversation(conversation_id):
            data = request.json
            closed_by = data.get("closed_by")
            closed_reason = data.get("closed_reason")
            with Session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                conversation.closed_by = closed_by
                conversation.closed_reason = closed_reason
                conversation.status = 'closed'
                # Update the status after checking the webhook notification
                session.query(IncomingMessage).filter_by(conversation_id=conversation_id).update(
                    {"status": "responded"}
                )
                session.commit()
                return jsonify({'status': 'success', 'message': 'Conversation closed successfully'}), 200

        @app.route('/chat/conversations/new', methods=['POST'])
        @cross_origin()
        def new_conversation():
            data = request.json
            organization_id = data.get('organization_id')
            platform_id = data.get('platform_id')
            contact_id = data.get('contact_id')
            user_id = data.get('user_id')
            with Session() as session:
                conversation = session.query(Conversation).filter_by(
                    organization_id=organization_id,
                    platform_id=platform_id,
                    contact_id=contact_id).filter(Conversation.status.in_(['new', 'active'])).first()
                if conversation:
                    return jsonify({'error': 'Conversation already open / active'}), 400
                username = session.query(User).filter_by(id=user_id).first().name
                conversation = Conversation(
                    organization_id=organization_id,
                    platform_id=platform_id,
                    contact_id=contact_id,
                    assigned_user_id=user_id,
                    open_by=username,
                    status="active"
                )
                session.add(conversation)
                session.commit()
                return jsonify({'id': conversation.id}), 200
        
        def get_date_range(filter_type):
            today = datetime.today()
            if filter_type == 'daily':
                # 24-hour period from today
                start_date = today - timedelta(days=1)  # 1 day ago
                end_date = today
            elif filter_type == 'weekly':
                # 7 days from today (last 7 days)
                start_date = today - timedelta(days=7)
                end_date = today
            elif filter_type == 'monthly':
                # Last 30 days from today
                start_date = today - timedelta(days=30)
                end_date = today
            elif filter_type == 'quarterly':
                # Last 3 months (approx 90 days)
                start_date = today - timedelta(days=90)
                end_date = today
            elif filter_type == 'halfyearly':
                # Last 6 months (approx 180 days)
                start_date = today - timedelta(days=180)
                end_date = today
            elif filter_type == 'yearly':
                # Last 365 days from today
                start_date = today - timedelta(days=365)
                end_date = today
            else:
                raise ValueError("Invalid filter type. Must be 'daily', 'weekly', 'monthly', or 'yearly'.")
            return start_date, end_date

        def get_grouping_interval(filter_type):
            """
            Returns the appropriate SQL grouping function based on filter_type (daily, weekly, etc.)
            """
            if filter_type == 'daily':
                return func.date(Conversation.updated_at)  # Group by day
            elif filter_type == 'weekly':
                return func.strftime('%Y-%W', Conversation.updated_at)  # Group by week
            elif filter_type == 'monthly':
                return func.strftime('%Y-%m', Conversation.updated_at)  # Group by month
            elif filter_type == 'yearly':
                return func.strftime('%Y', Conversation.updated_at)  # Group by year
            elif filter_type == 'quarterly':
                return func.strftime('%Y-%m', Conversation.updated_at)  # Group by quarter
            elif filter_type == 'halfyearly':
                return func.case(
                    [
                        (func.strftime('%m', Conversation.updated_at).in_([1, 2, 3, 4, 5, 6]), 'H1'),
                        (func.strftime('%m', Conversation.updated_at).in_([7, 8, 9, 10, 11, 12]), 'H2'),
                    ],
                    else_='Unknown'
                )  # Group by half-year (H1 or H2)
            else:
                raise ValueError('Invalid filter type')
        
        def period_labels(label):
            def parse_week(iso_week):
                year, week = iso_week.split('-')
                year, week = int(year), int(week)
                return f"{year} - Week {week}"
            period = {
                'daily': lambda date: f"Day {datetime.strptime(date, '%Y-%m-%d').day}",
                'weekly': lambda date: parse_week(date),
                'monthly': lambda date: f"{datetime.strptime(date, '%Y-%m').year} - Month {datetime.strptime(date, '%Y-%m').month}",
                'yearly': lambda date: f"Y {datetime.strptime(date, '%Y').year}",
                'quarterly': lambda date: f"{datetime.strptime(date, '%Y-%m').year} - Q{((datetime.strptime(date, '%Y-%m').month - 1) // 3) + 1} {datetime.strptime(date, '%Y-%m').year}" if date is not None else 'Q',
                'halfyearly': lambda date: 'H1' if datetime.strptime(date, '%m').month <= 6 else 'H2' if date is not None else 'H',
            }
            return period[label]


        @app.route('/chat/conversations/metrics/org', methods=['GET'])
        @cross_origin()
        def get_conversation_metrics_org():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({"error": "Organization Id required"}), 400
            duration = request.args.get('duration', None)  # 'daily', 'weekly', 'monthly', etc.
            period = request.args.get('period', 'daily')
            start_date = request.args.get('start_date')  # Optional: YYYY-MM-DD
            end_date = request.args.get('end_date')  # Optional: YYYY-MM-DD
            # Determine the date range based on the filter
            if duration:
                try:
                    start_date, end_date = get_date_range(duration)
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            print(start_date, end_date)
            
            with Session() as session:
                # Grouping the data by the selected time period
                grouping_interval = get_grouping_interval(period)
                # Query for user performance stats grouped by the selected period
                user_performance_stats = session.query(
                    grouping_interval.label('period'),
                    func.count().label('total_assigned'),
                    func.count(case((Conversation.status == 'closed', 1), else_=None)).label('total_closed'),
                    func.count(case((Conversation.status == 'active', 1), else_=None)).label('total_active')
                ).filter(
                    Conversation.organization_id == organization_id,
                    Conversation.assigned_user_id != None,
                    Conversation.updated_at.between(start_date, end_date)
                ).group_by(
                    grouping_interval,
                ).order_by(
                    grouping_interval,
                    func.count(case((Conversation.status == 'closed', 1), else_=None)).desc()
                ).all()
        
                # Structure the response
                response = {
                    'org_performance_stats': [
                        {
                            'label': period_labels(period)(stat[0]),  # Convert to readable date format,
                            'total_assigned': stat[1],
                            'total_closed': stat[2],
                            'total_active': stat[3]
                        }
                        for stat in user_performance_stats
                    ]
                }
                return jsonify(response)
        
        @app.route('/chat/conversations/metrics/employee', methods=['GET'])
        @cross_origin()
        def get_conversation_metrics_employee():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({"error": "Organization Id required"}), 400
            
            duration = request.args.get('duration', None)  # 'daily', 'weekly', 'monthly', etc.
            period = request.args.get('period', 'daily')
            start_date = request.args.get('start_date')  # Optional: YYYY-MM-DD
            end_date = request.args.get('end_date')  # Optional: YYYY-MM-DD
            
            # Determine the date range based on the filter
            if duration:
                try:
                    start_date, end_date = get_date_range(duration)
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            print(start_date, end_date)
            
            with Session() as session:
                # Grouping the data by the selected time period
                grouping_interval = get_grouping_interval(period)
                print(grouping_interval)
                
                # Query for user performance stats grouped by the selected period
                user_performance_stats = session.query(
                    grouping_interval.label('period'),
                    Conversation.assigned_user_id,
                    func.count().label('total_assigned'),
                    func.count(case((Conversation.status == 'closed', 1), else_=None)).label('total_closed'),
                    func.count(case((Conversation.status == 'active', 1), else_=None)).label('total_active')
                ).filter(
                    Conversation.organization_id == organization_id,
                    Conversation.assigned_user_id != None,
                    Conversation.updated_at.between(start_date, end_date)
                ).group_by(
                    grouping_interval,
                    Conversation.assigned_user_id
                ).order_by(
                    grouping_interval,
                    func.count(case((Conversation.status == 'closed', 1), else_=None)).desc()
                ).all()
        
                # Structure the response
                response = {
                    'user_performance_stats': [
                        {
                            'label': period_labels(period)(stat[0]),  # Convert to readable date format,
                            'assigned_user_id': stat[1],
                            'total_assigned': stat[2],
                            'total_closed': stat[3],
                            'total_active': stat[4]
                        }
                        for stat in user_performance_stats
                    ]
                }
                
                return jsonify(response)


        @app.route('/chat/conversations/stats', methods=['GET'])
        @cross_origin()
        def get_conversation_stats():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({"error": "Orgaization Id required"}), 400
            # Get filter parameters
            filter_type = request.args.get('filter', 'daily')  # 'daily', 'weekly', 'monthly'
            start_date = request.args.get('start_date')  # Optional: YYYY-MM-DD
            end_date = request.args.get('end_date')  # Optional: YYYY-MM-DD
            # Determine the date range based on the filter
            try:
                start_date, end_date = get_date_range(filter_type)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            # Parse dates if provided as strings
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            with Session() as session:
                print(start_date, end_date)
                # Query the database
                total_new = session.query(func.count()).filter(
                    Conversation.organization_id == organization_id,
                ).scalar()
                total_closed = session.query(func.count()).filter(
                    Conversation.organization_id == organization_id,
                    Conversation.status == 'closed',
                    Conversation.updated_at.between(start_date, end_date)
                ).scalar()
                total_active = session.query(func.count()).filter(
                    Conversation.organization_id == organization_id,
                    Conversation.status == 'active',
                    Conversation.updated_at.between(start_date, end_date)
                ).scalar()

                # Per contact_id stats (frequency of communication and services used)
                per_contact_stats = session.query(
                    Conversation.contact_id,
                    func.count().label('communication_count'),
                    func.count(func.distinct(Conversation.platform_id)).label('services_used')
                ).filter(Conversation.organization_id == organization_id, Conversation.updated_at.between(start_date, end_date)).group_by(Conversation.contact_id).all()
                # Services used breakdown by platform_id for each contact_id
                services_used_stats = session.query(
                    Conversation.contact_id,
                    Platform.platform_name,
                    func.count().label('conversation_count')
                ).join(
                    Platform, Platform.id == Conversation.platform_id
                ).filter(
                    Conversation.organization_id == organization_id,
                    Conversation.updated_at.between(start_date, end_date)
                ).group_by(
                    Conversation.contact_id,
                    Platform.platform_name
                ).all()

                # Performance stats queries here, using start_date and end_date
                user_performance_stats = session.query(
                    Conversation.assigned_user_id,
                    func.count().label('total_active'),
                    func.count(case((Conversation.status == 'closed', 1), else_=None)).label('total_closed'),
                    func.count(case((Conversation.status == 'active', 1), else_=None)).label('total_active')
                ).filter(
                    Conversation.organization_id == organization_id,
                    Conversation.assigned_user_id != None,
                    Conversation.updated_at.between(start_date, end_date)
                ).group_by(
                    Conversation.assigned_user_id
                ).order_by(
                    func.count(case((Conversation.status == 'closed', 1), else_=None)).desc()
                ).all()

                # Average response time
                average_response_time = session.query(
                    func.avg(
                        (func.julianday(UserMessage.sent_time) - func.julianday(IncomingMessage.received_time)) * 86400
                    ).label("average_response_time")
                ).select_from(
                    IncomingMessage
                ).join(
                    UserMessage,
                    UserMessage.conversation_id == IncomingMessage.conversation_id
                ).filter(
                    IncomingMessage.received_time.between(start_date, end_date),
                    UserMessage.sent_time > IncomingMessage.received_time
                ).scalar()

                response_time_per_employee = session.query(
                    UserMessage.user_id,
                    func.avg(
                        (func.julianday(UserMessage.sent_time) - func.julianday(IncomingMessage.received_time)) * 86400
                    ).label("average_response_time")
                ).select_from(
                    IncomingMessage
                ).join(
                    UserMessage, UserMessage.conversation_id == IncomingMessage.conversation_id
                ).filter(
                    UserMessage.sent_time > IncomingMessage.received_time,
                    IncomingMessage.received_time.between(start_date, end_date)
                ).group_by(
                    UserMessage.user_id
                ).all()

                # Resolution time
                subquery = session.query(
                    Conversation.assigned_user_id,
                    (func.count(case((Conversation.status == 'closed', 1), else_=None)) * 1.0 /
                     func.count(Conversation.id)).label('resolution_rate')
                ).filter(
                    Conversation.assigned_user_id != None,
                    Conversation.updated_at.between(start_date, end_date)
                ).group_by(
                    Conversation.assigned_user_id
                ).subquery()
                
                # Main query: Calculate the average resolution rate
                average_resolution_rate = session.query(
                    func.avg(subquery.c.resolution_rate).label('average_resolution_rate')
                ).scalar()


                # Subquery to calculate resolution time for each conversation
                resolution_time_subquery = session.query(
                    Conversation.id.label('conversation_id'),
                    ((func.julianday(func.max(UserMessage.sent_time)) - func.julianday(func.min(IncomingMessage.received_time))) * 86400)
                    .label('resolution_time')
                ).join(
                    IncomingMessage, IncomingMessage.conversation_id == Conversation.id
                ).join(
                    UserMessage, UserMessage.conversation_id == Conversation.id
                ).filter(
                    Conversation.status == 'closed',  # Only closed conversations
                    IncomingMessage.received_time.between(start_date, end_date)  # Date range filter
                ).group_by(Conversation.id).subquery()
                
                # Main query to calculate the average resolution time
                average_resolution_time = session.query(
                    func.avg(resolution_time_subquery.c.resolution_time).label('average_resolution_time')
                ).scalar()

                # Subquery to calculate resolution time for each conversation per employee
                resolution_time_per_employee_subquery = session.query(
                    UserMessage.user_id,
                    ((func.julianday(func.max(UserMessage.sent_time)) - func.julianday(func.min(IncomingMessage.received_time))) * 86400)
                    .label('resolution_time')
                ).join(
                    IncomingMessage, IncomingMessage.conversation_id == UserMessage.conversation_id
                ).filter(
                    Conversation.status == 'closed',  # Only closed conversations
                    IncomingMessage.received_time.between(start_date, end_date)  # Date range filter
                ).group_by(UserMessage.user_id, UserMessage.conversation_id).subquery()

                # Main query to calculate average resolution time per employee
                resolution_time_per_employee = session.query(
                    resolution_time_per_employee_subquery.c.user_id,
                    func.avg(resolution_time_per_employee_subquery.c.resolution_time).label('average_resolution_time')
                ).group_by(resolution_time_per_employee_subquery.c.user_id).all()

                # Structure the response
                response = {
                    'total_new': total_new,
                    'total_closed': total_closed,
                    'total_active': total_active,
                    'customer_performance_stats': [
                        {
                            'contact_id': stat[0],
                            'services_used': [
                                {'platform_name': platform_name, 'conversation_count': count}
                                for (contact_id, platform_name, count) in services_used_stats if contact_id == stat[0]
                            ]
                        }
                        for stat in per_contact_stats
                    ],
                    'user_performance_stats': [
                        {'user_id': stat[0], 'total_active': stat[1], 'total_closed': stat[2]}
                        for stat in user_performance_stats
                    ],
                    'user_performance_stats_avg': {
                        'average_response_time': round((average_response_time / (60 * 60)), 2) if average_response_time is not None else 0,
                        'response_time_per_employee': [{'user_id': resp_time[0], 'avg': resp_time[1]} for resp_time in response_time_per_employee],
                        'average_resolution_rate': round(average_resolution_rate, 2) * 100 if average_resolution_rate is not None else 0,
                        'average_resolution_time': round((average_resolution_time / (60 * 60)), 2) if average_resolution_time is not None else 0,
                        'resolution_time_per_employee': [{'user_id': res_time[0], 'avg': res_time[1]} for res_time in resolution_time_per_employee]                        
                    }
                }
                return jsonify(response)
    return app
