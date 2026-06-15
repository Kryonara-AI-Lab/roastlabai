from app import create_app

app = create_app()

if __name__ == '__main__':
    # Starts the application on debug mode for rapid prototyping
    app.run(debug=True)