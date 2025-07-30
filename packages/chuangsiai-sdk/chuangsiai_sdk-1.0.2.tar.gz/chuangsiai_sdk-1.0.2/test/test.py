from chuangsiai_sdk import ChuangsiaiClient

def main():
    client = ChuangsiaiClient(api_key="apikey_d998e03048a696a41c676384d2a0a5b6")

    resp =  client.input_guardrail(strategyKey="669358997282885", content="测试内容")

    print(resp)

if __name__ == "__main__":
    main()