import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler,
    ContextTypes
)

# Constants for conversation states
ROLL_NO, COMMAND_SELECTION = range(2)

# Replace with your bot token
BOT_TOKEN = '6714168137:AAFtogev7ibGldZLE1CGUzsL2w95jbQH8cw'

# Database connection


def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anu@1234",
        database="attendance_db"
    )

# Handler for the /hello command


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

# Command handler to start the bot and ask for roll number


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Please enter your roll number:")
    return ROLL_NO

# Handle roll number input and provide options


async def roll_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll_no = update.message.text.strip()
    context.user_data['roll_no'] = roll_no  # Save roll number to user data

    # Offer options after roll number input
    keyboard = [
        [
            InlineKeyboardButton("Total Attendance",
                                 callback_data='attendance'),
            InlineKeyboardButton("Subject-wise Attendance",
                                 callback_data='subject')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please select an option:", reply_markup=reply_markup)

    return COMMAND_SELECTION

# Command handler to fetch total attendance


async def total_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll_no = context.user_data.get('roll_no', None)

    try:
        # Connect to the database
        db_connection = connect_to_database()
        cursor = db_connection.cursor(dictionary=True)

        # Query to fetch average attendance for the given roll number
        query = "SELECT average_attendance FROM subject_attendance WHERE roll_no = %s"
        cursor.execute(query, (roll_no,))
        result = cursor.fetchone()

        if result:
            await update.callback_query.message.reply_text(f"Attendance: {result['average_attendance']}%")
        else:
            await update.callback_query.message.reply_text("Roll number does not match our records.")

        # Ensure all results are fetched
        cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"MySQL error: {str(e)}")  # Log the MySQL error
        await update.callback_query.message.reply_text(f"An error occurred while fetching attendance: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Log unexpected errors
        await update.callback_query.message.reply_text(f"An unexpected error occurred: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()

# Command handler to fetch subject-wise attendance


async def subject_wise_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll_no = context.user_data.get('roll_no', None)

    try:
        # Connect to the database
        db_connection = connect_to_database()
        cursor = db_connection.cursor(dictionary=True)

        # Query to fetch subject-wise attendance for the given roll number
        query = "SELECT subject_name, percentage_over_sessions, sessions_rem FROM subject_attendance WHERE roll_no = %s"
        cursor.execute(query, (roll_no,))
        results = cursor.fetchall()

        if results:
            response = ""
            for result in results:
                subject_name = result['subject_name']
                percentage = result['percentage_over_sessions']
                sessions_rem = result['sessions_rem']

                # Calculate the satisfaction status based on percentage and sessions remaining
                if percentage >= 75:
                    satisfaction = "Satisfactory"
                else:
                    satisfaction = f"You current attendance is {result['percentage_over_sessions']}% for\ngetting atleast 75.0% you need to\nattend more {sessions_rem} classes!!"

                # Construct the response message
                response += f"<b>{subject_name}:</b> {percentage}%\n{satisfaction}\n\n"

            await update.callback_query.message.reply_text(response, parse_mode='HTML')
        else:
            await update.callback_query.message.reply_text("No subject-wise attendance found.")
    except mysql.connector.Error as e:
        print(f"MySQL error: {str(e)}")  # Log the MySQL error
        await update.callback_query.message.reply_text(f"An error occurred while fetching subject-wise attendance: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Log unexpected errors
        await update.callback_query.message.reply_text(f"An unexpected error occurred: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()

# Callback query handler


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'attendance':
        await total_attendance(update, context)
    elif query.data == 'subject':
        await subject_wise_attendance(update, context)

# Command handler to cancel the conversation


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

# Main function to set up the bot


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROLL_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, roll_no)],
            COMMAND_SELECTION: [CallbackQueryHandler(button)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(conv_handler)

    # Run the bot indefinitely
    app.run_polling()


if _name_ == '_main_':
    main()
