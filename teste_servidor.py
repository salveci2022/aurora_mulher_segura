from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ SERVIDOR AURORA FUNCIONANDO!"

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 TESTE DO SERVIDOR")
    print("="*50)
    print("Acesse no navegador:")
    print("  • http://localhost:5000")
    print("  • http://192.168.15.93:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)