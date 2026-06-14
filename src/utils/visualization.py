def save_graph_png(app, filename="lexguard_architecture.png"):
    try:
        with open(filename, "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print(f"📸 Graph saved as {filename}")
    except Exception as e:
        print(f"⚠️ Could not generate graph image: {e}")