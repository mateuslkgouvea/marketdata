import uvicorn

def main():
    uvicorn.run(
        'marketdata:app',
        host = '0.0.0.0',
        port = 5000,
        reload = True)

if __name__ == '__main__':
    main()