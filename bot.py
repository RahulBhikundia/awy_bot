import logging
import boto3
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler


# Define conversation states
AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION = range(3)
IMAGE_ID, INSTANCE_TYPE, KEY_NAME = range(3)
INSTANCE_ID = range(0)
# Initialize a dictionary to store user data
user_data = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""Awy welcomes you! Awy is a cloud helper( more accurately ec2 helper). With Awy, you can-
        1. Create an instance
        2. View Running Instance
        3. Stop an instance
        4. Terminate an instance
        (Note: To begin with you must have an AWS account)

        You can use following commands to get started with Awy-
        1. '/login'  - To login to your AWS account
        2. '/create' - To create an instance
        3. '/view'   - To view Running Instance
        4. '/stop'   - To stop an instance
        5. '/terminate' - To terminate an instance """
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


async def aws_login(update: Update, context):
    # Ask for AWS Access Key ID
    await update.message.reply_text("Please enter your AWS Access Key ID:")
    return AWS_ACCESS_KEY


async def get_aws_access_key(update: Update, context):
    aws_access_key_id = update.message.text
    user_data['aws_access_key_id'] = aws_access_key_id

    # Ask for AWS Secret Access Key
    await update.message.reply_text("Please enter your AWS Secret Access Key:")
    return AWS_SECRET_KEY


async def get_aws_secret_key(update: Update, context):
    aws_secret_access_key = update.message.text
    user_data['aws_secret_access_key'] = aws_secret_access_key

    # Ask for AWS region
    await update.message.reply_text("Please enter your AWS region:")
    return REGION


async def get_region(update: Update, context):
    region = update.message.text
    user_data['region'] = region

    aws_access_key_id = user_data.get('aws_access_key_id')
    aws_secret_access_key = user_data.get('aws_secret_access_key')
    region = user_data.get('region')
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region
    )

    user_data['ec2'] = session.resource('ec2')
    await update.message.reply_text("AWS Login Successful")
    return ConversationHandler.END


async def cancelLogin(update: Update, context):
    # End the conversation
    await update.message.reply_text("AWS login canceled.")
    return ConversationHandler.END


async def createInstance(update: Update, context):
    await update.message.reply_text("Please type in asked information:")
    await update.message.reply_text("Image ID")
    return IMAGE_ID


async def get_image_id(update: Update, context):
    aws_image_id = update.message.text
    user_data['aws_image_id'] = aws_image_id

    # Instance Type
    await update.message.reply_text("Instance Type")
    return INSTANCE_TYPE


async def get_instance_type(update: Update, context):
    aws_instance_type = update.message.text
    user_data['aws_instance_type'] = aws_instance_type

    # Key Name
    await update.message.reply_text("Key Name")
    return KEY_NAME


async def get_key_name(update: Update, context):
    aws_key_name = update.message.text
    user_data['aws_key_name'] = aws_key_name

    aws_image_id = user_data.get('aws_image_id')
    aws_instance_type = user_data.get('aws_instance_type')
    aws_key_name = user_data.get('aws_key_name')

    if aws_image_id and aws_instance_type and aws_key_name:
        instance_params = {
            'ImageId': aws_image_id,  # Correct the parameter names
            'InstanceType': aws_instance_type,  # Correct the parameter names
            'KeyName': aws_key_name,  # Correct the parameter names
            'MinCount': 1,
            'MaxCount': 1
        }

        # Access the ec2 object from the user context
        ec2 = user_data['ec2']

        instance = ec2.create_instances(**instance_params)[0]
        await update.message.reply_text(f"Created EC2 instance with ID: {instance.id}")
    else:
        await update.message.reply_text("Please provide all required information before creating the instance.")

    return ConversationHandler.END


async def cancelCreate(update: Update, context):
    # End the conversation
    await update.message.reply_text("Instance Cannot be created")
    return ConversationHandler.END


async def viewHandler(update: Update, context):
    ec2 = user_data['ec2']
    instances = ec2.instances.all()
    for instance in instances:
        await update.message.reply_text(f"Instance ID: {instance.id}")
        await update.message.reply_text(f"Instance State: {instance.state['Name']}")
        await update.message.reply_text(f"Instance Type: {instance.instance_type}")
        await update.message.reply_text(f"Public IP Address: {instance.public_ip_address}")
        await update.message.reply_text(f"Private IP Address: {instance.private_ip_address}")
        await update.message.reply_text("----------------------------")


async def stopHandler(update: Update, context):
    await update.message.reply_text("Type the instance id for the instance which you want to stop:")
    return INSTANCE_ID


async def get_instance_id_stop(update: Update, context):
    instance_id = update.message.text
    user_data['ec2'].Instance(instance_id).stop()
    await update.message.reply_text(f"Instance with instance id {instance_id} has been succefully STOPPED")
    return ConversationHandler.END


async def cancelStop(update: Update, context):
    await update.message.reply_text("Instance Cannot be stopped")
    return ConversationHandler.END


async def terminateHandler(update: Update, context):
    await update.message.reply_text("Type the instance id for the instance which you want to delete:")
    return INSTANCE_ID


async def get_instance_id_term(update: Update, context):
    instance_id = update.message.text
    user_data['ec2'].Instance(instance_id).terminate()
    await update.message.reply_text(f"Instance with instance id {instance_id} has been succefully Terminated")
    return ConversationHandler.END


async def cancelTerminate(update: Update, context):
    await update.message.reply_text("Instance Cannot be terminated")
    return ConversationHandler.END


if __name__ == '__main__':
    application = ApplicationBuilder().token(
        '6725994049:AAETW9sN5tk9-DSA7ZPsX7rR72YU_RPBL3s').build()

    start_handler = CommandHandler('start', start)
    # echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    aws_login_handler = ConversationHandler(
        entry_points=[CommandHandler('login', aws_login)],
        states={
            AWS_ACCESS_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_aws_access_key)],
            AWS_SECRET_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_aws_secret_key)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region)],
        },
        fallbacks=[CommandHandler('cancel', cancelLogin)]
    )

    create_handler = ConversationHandler(
        entry_points=[CommandHandler('create', createInstance)],
        states={
            IMAGE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_image_id)],
            INSTANCE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_instance_type)],
            KEY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_key_name)],
        },
        fallbacks=[CommandHandler('cancel', cancelCreate)]
    )

    view_handler = CommandHandler('view', viewHandler)

    stop_handler = ConversationHandler(
        entry_points=[CommandHandler('stop', stopHandler)],
        states={
            INSTANCE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_instance_id_stop)],
        },
        fallbacks=[CommandHandler('cancel', cancelStop)],
    )

    terminate_handler = ConversationHandler(
        entry_points=[CommandHandler('terminate', terminateHandler)],
        states={
            INSTANCE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_instance_id_term)],
        },
        fallbacks=[CommandHandler('cancel', cancelTerminate)],
    )

    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(aws_login_handler)
    application.add_handler(create_handler)
    application.add_handler(view_handler)
    application.add_handler(stop_handler)
    application.add_handler(terminate_handler)
    application.add_handler(unknown_handler)
    application.run_polling()
