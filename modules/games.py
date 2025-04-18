from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest

import random
import json
import time
from .sql import games_sql as sql

# Trivia questions database (example)
TRIVIA_QUESTIONS = [
    {
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "correct": 2
    },
    # Add more questions...
]

class WordChainGame:
    def __init__(self):
        self.current_word = ""
        self.used_words = set()
        self.current_player = None
        self.players = []
        self.start_time = None

    def start(self, first_word, first_player):
        self.current_word = first_word
        self.used_words.add(first_word)
        self.current_player = first_player
        self.players.append(first_player)
        self.start_time = time.time()

    def is_valid_word(self, word):
        if word in self.used_words:
            return False
        if not word.startswith(self.current_word[-1]):
            return False
        return True  # You might want to add a dictionary check here

def dice(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    result = random.randint(1, 6)
    message.reply_dice()
    
    # Update user's score
    new_score = sql.update_score(chat.id, user.id, result)
    message.reply_text(
        f"🎲 {user.mention_html()} rolled a {result}!\n"
        f"Total score: {new_score}",
        parse_mode=ParseMode.HTML
    )

def trivia(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    # Select random question
    question = random.choice(TRIVIA_QUESTIONS)
    
    # Create keyboard with options
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([
            InlineKeyboardButton(
                option,
                callback_data=f"trivia_{i}_{question['correct']}"
            )
        ])
        
    message.reply_text(
        f"📝 *Trivia Question:*\n\n{question['question']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def trivia_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    
    selected, correct = map(int, query.data.split('_')[1:])
    
    if selected == correct:
        points = 5
        result = "Correct! 🎉"
    else:
        points = -2
        result = f"Wrong! The correct answer was: {TRIVIA_QUESTIONS[0]['options'][correct]}"
    
    new_score = sql.update_score(chat.id, user.id, points)
    
    query.answer(f"{result} ({'+' if points > 0 else ''}{points} points)")
    query.message.edit_text(
        f"{result}\n{user.mention_html()} now has {new_score} points!",
        parse_mode=ParseMode.HTML
    )

def word_chain(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    if not hasattr(context.bot_data, 'word_games'):
        context.bot_data['word_games'] = {}
    
    if chat.id not in context.bot_data['word_games']:
        if not args:
            message.reply_text("Please provide a word to start the game!")
            return
            
        game = WordChainGame()
        game.start(args[0].lower(), user.id)
        context.bot_data['word_games'][chat.id] = game
        
        message.reply_text(
            f"Word Chain game started by {user.mention_html()}!\n"
            f"Current word: *{args[0]}*\n"
            "Reply with a word that starts with the last letter!",
            parse_mode=ParseMode.HTML
        )
    else:
        message.reply_text("A game is already in progress!")

def handle_word(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    if not hasattr(context.bot_data, 'word_games'):
        return
        
    game = context.bot_data['word_games'].get(chat.id)
    if not game:
        return
        
    word = message.text.lower()
    
    if not game.is_valid_word(word):
        message.reply_text("Invalid word! Try again.")
        return
        
    game.current_word = word
    game.used_words.add(word)
    
    if user.id not in game.players:
        game.players.append(user.id)
    
    message.reply_text(
        f"Valid word! Next word must start with: *{word[-1]}*",
        parse_mode=ParseMode.MARKDOWN
    )

def game_leaderboard(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    top_players = sql.get_leaderboard(chat.id)
    
    if not top_players:
        message.reply_text("No game scores recorded yet!")
        return
        
    text = "🎮 *Game Leaderboard* 🏆\n\n"
    for i, player in enumerate(top_players, 1):
        try:
            member = chat.get_member(player.user_id)
            name = member.user.full_name
        except BadRequest:
            name = f"User {player.user_id}"
            
        text += f"{i}. {name}: {player.score} points ({player.games_played} games)\n"
        
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN) 