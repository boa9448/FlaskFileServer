import FileServer

app = FileServer.create_app()
app.run(debug=True)