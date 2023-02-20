from queue import Empty, Queue
import threading
import time
import uuid
from flask import Flask
from flask_restful import Resource, Api, fields, marshal_with, request
from revChatGPT.V1 import Chatbot
import logging
import logging.handlers as handlers
import os

app = Flask(__name__)
api = Api(app)


def worker_thread_function(bot):
    logger = logging.getLogger("worker_thread_function")
    logger.info("a worker thread started")
    while bot.is_working():
        try:
            bot.start_answering()
        except Empty:
            pass
        except Exception as e: 
            logger.error(e, exc_info=True)
            time.sleep(1)
    logger.info("a worker thread stopped")

def initialize_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logHandler = handlers.TimedRotatingFileHandler('logs/server.log', when='D', interval=1)
    logHandler.setLevel(logging.INFO)
    ## Here we set our logHandler's formatter
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    
    logHandler = logging.StreamHandler()
    logger.addHandler(logHandler)
    
    
class Question:
    def __init__(self, text, conversation_id=None, parent_id=None):
        self.text = text
        self.conversation_id = conversation_id
        self.parent_id = parent_id
        self.question_id = str(uuid.uuid4())


class Answer:
    def __init__(self, text, conversation_id, parent_id, finished):
        self.text = text
        self.conversation_id = conversation_id
        self.parent_id = parent_id
        self.finished = finished


class Bot:
    def __init__(self, num_worker_threads):
        self.question_queue = Queue()
        self.answer_queues = {}
        self.answer_queues_lock = threading.Lock()
        self.worker_threads = []
        self.working = True
        self.num_worker_threads = num_worker_threads
        self.access_token = None

        self.answer_queue_max_size = 64
        self.ask_timeout = 10
        self.logger = logging.getLogger(Bot.__name__)

    def start(self):
        for x in range(self.num_worker_threads):
            t = threading.Thread(target=worker_thread_function, args=(self,))
            self.worker_threads.append(t)
            t.start()

    def set_acccess_token(self, access_token):
        self.access_token = access_token

    def stop(self):
        self.working = False
        for t in self.worker_threads:
            t.join(5)

    def is_working(self):
        return self.working

    def start_answering(self):
        question = self.question_queue.get(block=True, timeout=1)
        self.question_queue.task_done()

        if not question or not isinstance(question, Question):
            return
        # self.logger.info("received a question, %s, %s", question.text, question.question_id)
        chatbot = Chatbot(config={
            "access_token": self.access_token
        })

        text_pos = 0
        self.logger.info("asking, %s, %s, %s, %s", question.question_id, question.conversation_id, question.parent_id, question.text)
        try:
            for data in chatbot.ask(question.text, conversation_id=question.conversation_id, parent_id=question.parent_id, timeout=self.ask_timeout):
                message = data["message"][text_pos:]
                text_pos = len(data["message"])
                answer = Answer(
                    message, data["conversation_id"], data["parent_id"], False)
                self.queue_answer(question.question_id, answer)
                self.logger.info("receiving answer, %s, %s, %s, %s", message, question.question_id, data["conversation_id"], data["parent_id"])
            self.logger.info("answer complete, %s, %s", question.question_id, data)
            answer = Answer(None, data["conversation_id"], data["parent_id"], True)
            self.queue_answer(question.question_id, answer)
        except Exception as ex:
            answer = Answer(str(ex), None, None, False)
            answer = Answer(None, None, None, True)
            self.queue_answer(question.question_id, answer)

    def queue_answer(self, question_id, answer):
        self.answer_queues_lock.acquire(blocking=True, timeout=1)
        try:
            aq = self.answer_queues.get(question_id)
            if aq is None:
                aq = Queue(maxsize=self.answer_queue_max_size)
                self.answer_queues[question_id] = aq
        finally:
             self.answer_queues_lock.release()
        aq.put(answer)
        

    def pop_answer(self, question_id):
        self.answer_queues_lock.acquire(blocking=True, timeout=1)
        aq = self.answer_queues.get(question_id)
        self.answer_queues_lock.release()

        if aq is None:
            self.logger.warning("no answer queue found, %s", question_id)
            
            return Answer(None, None, None, False)

        text = ""
        conversation_id = None
        parent_id = None
        finished = False
        while True:
            try:
                answer = aq.get(block=False)
                aq.task_done()
            except Empty:
                answer = None
            if answer is None:
                break
            self.logger.info("popping answer: %s, %s, %s, %s", answer, answer.conversation_id, answer.parent_id, answer.text)
            finished = answer.finished
            if not finished:
                conversation_id = answer.conversation_id
                parent_id = answer.parent_id
                text += answer.text
        
        if finished:
            self.answer_queues.pop(question_id, None)
        
        answer = Answer(text, conversation_id, parent_id, finished)
        return answer

    def ask(self, text, conversation_id, parent_id):
        question = Question(text, conversation_id, parent_id)
        self.question_queue.put(question)
        return question


answer_fields = {
    'text': fields.String,
    'conversation_id': fields.String,
    'parent_id': fields.String,
    'finished': fields.Boolean
}

question_fields = {
    'question_id': fields.String
}


class QuestionApi(Resource):
    @marshal_with(question_fields, envelope="data")
    def post(self):
        json_data = request.get_json()
        text = json_data.get("text")
        conversation_id = json_data.get("conversation_id")
        parent_id = json_data.get("parent_id")
        question = bot.ask(text, conversation_id, parent_id)
        return question

class AnswerApi(Resource):
    @marshal_with(answer_fields, envelope="data")
    def get(self):
        args = request.args
        question_id = args.get("question_id")
        answer = bot.pop_answer(question_id)
        return answer


api.add_resource(QuestionApi, '/chatgpt/api/questions')
api.add_resource(AnswerApi, '/chatgpt/api/answers')


if __name__ == '__main__':
    initialize_logging()
    
    num_worker_threads = os.environ.get("NUM_WORKER_THREADS") or 4
    num_worker_threads = int(num_worker_threads)
    bot = Bot(num_worker_threads)
    bot.access_token = os.environ.get("ACCESS_TOKEN")
    bot.start()
    app.run(host="0.0.0.0", debug=True)
    bot.stop()
