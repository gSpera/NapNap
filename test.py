from flask import Flask
app=Flask("Test")

@app.route("/")
def main():
	return "Test"
