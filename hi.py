from revChatGPT.V1 import Chatbot
def main():
    chatbot = Chatbot(config={
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJtYXppbWVuZ0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZ2VvaXBfY291bnRyeSI6IlVTIn0sImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJ1c2VyX2lkIjoidXNlci1SbllDZlEySndVTERJOXFSMjlxdFJYZUIifSwiaXNzIjoiaHR0cHM6Ly9hdXRoMC5vcGVuYWkuY29tLyIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTA4NjQ2NTczNjY1MjE5NzU2MjI2IiwiYXVkIjpbImh0dHBzOi8vYXBpLm9wZW5haS5jb20vdjEiLCJodHRwczovL29wZW5haS5vcGVuYWkuYXV0aDBhcHAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTY3Njc5NDc4MSwiZXhwIjoxNjc4MDA0MzgxLCJhenAiOiJUZEpJY2JlMTZXb1RIdE45NW55eXdoNUU0eU9vNkl0RyIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgbW9kZWwucmVhZCBtb2RlbC5yZXF1ZXN0IG9yZ2FuaXphdGlvbi5yZWFkIG9mZmxpbmVfYWNjZXNzIn0.e4oa71iCzzLP8O8ib0dMIAHkJewxDRi0IfZx-GMsoHx4Ww6l6TqvqbYNj2VT2wUGbX-sowC8yyjC6aqrz5OypiDES0e9GJleFHxrmNzLs9kHCuEXs9PhWiuDDPv5loQebVGU5DKA1UVVeS1MDt2pTSssJvz4Q4QQd1QVeOSDNQiHP-0vAhPg1zIWkNnlIxZRCtzJP8CnLkDBMo6PemDQbJC6Pg7Iz4Jicm1SnDoQJmDvMf0lh6Ee0ncrtd1fwWQBNKMQyT3iSss3DsDY7mD64qRK2VFiYXKBMeySlJ9D45YIWG_1nH7aUcEOdjn2I3BYKMNcX6jt3olaTfOz26dD6g"
    })
    
    conversation_id = "f54fc8a4-60a8-4e9d-84cf-1ea3be98b9f2"
    parent_id = "288c6ddb-1e80-41c5-82d7-6de35d5531f0"

    conversation_id = None
    parent_id = None

    print("Chatbot: ")
    asks = ["sorry what was my last question?"]
    for text in asks:
        text_pos = 0
        for data in chatbot.ask(text, conversation_id=conversation_id, parent_id=parent_id):
            message = data["message"][text_pos:]
            print(message, end="", flush=True)
            text_pos = len(data["message"])
        parent_id = data["parent_id"]
        print(data)

main()
