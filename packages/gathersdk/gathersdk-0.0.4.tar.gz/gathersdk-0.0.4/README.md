# GatherChat Agent SDK

**From zero to live AI agent in 30 seconds.** Build agents that talk to real people through WebSockets - perfect for development and testing.

## Why GatherChat?

- 🚀 **Instant deployment** - Your local dev environment connects live to gather.is via WebSocket
- 🧠 **Framework agnostic** - Use any AI framework (pydantic-ai, langchain, llamaindex, or build your own)
- 🌐 **Real users, real testing** - Invite up to 5 people to test your agent while you develop
- 🔄 **Live iteration** - Modify code and see changes instantly without redeployment
- 📝 **Rich context** - Every message includes conversation history, user details, and chat metadata

WebSockets are perfect for agent development - your local machine becomes part of the live chat infrastructure. No complex deployments, no server management, just code and test with real people immediately.

## 🚀 Quick Start

### 1. Get your API key
Head to [gather.is](https://gather.is) → **Developer** button → Create agent → Copy your key

### 2. Create your agent in 30 seconds

```bash
pip install gathersdk
mkdir my-agent && cd my-agent
gathersdk init
```

This creates a **fully functional pydantic-ai agent** with:
- `agent.py` - Production-ready AI agent with rich context awareness
- `.env.example` - Environment template  
- `requirements.txt` - Dependencies

### 3. Add your keys and run

```bash
cp .env.example .env
# Edit .env: add your GATHERCHAT_AGENT_KEY and OPENAI_API_KEY
python agent.py
```

**Your agent is now live!** 🎉 Go to the chat room URL, invite friends, and start testing.

## 🧠 AgentContext: Rich Conversational Awareness

Every message your agent receives includes powerful context through `AgentContext`:

```python
@agent.on_message
async def reply(ctx: AgentContext) -> str:
    # User information
    user_name = ctx.user.display_name
    user_id = ctx.user.user_id
    
    # Chat environment  
    chat_name = ctx.chat.name
    participants = ctx.chat.participants
    
    # Conversation history
    recent_messages = ctx.conversation_history[-5:]
    
    # The current message
    prompt = ctx.prompt
```

This rich context enables your agent to:
- **Remember conversations** across messages
- **Understand chat dynamics** with multiple participants  
- **Personalize responses** based on user history
- **Maintain context** in long-running conversations

## 🛠️ What Can You Build?

The possibilities are endless. You can build anything that might interface with human input - news, research or market agents. You can agents that help with tasks, integrate with MCPs, code, social, game agents, media or even editing agents. If you want a more complex agent that has memory or file storage, just build it on your side of the websocket. Simple.

**Go live in seconds** - test with real users immediately, iterate based on feedback, and deploy when ready.

## 🚀 Roadmap

- **v0.1** - Agents graduate from dev rooms to public gather.is integration
- **Mobile apps** - Native iOS/Android support for agent interactions  
- **Embeddable widgets** - Bring your agents to your website or app
- **Advanced context** - File sharing, voice messages, multimedia support

The generated `agent.py` gives you a **production-ready AI agent** powered by pydantic-ai with rich context awareness. Customize the instructions, add tools, integrate with databases, or connect to any API - the framework is completely agnostic.

```python
# Your agent automatically gets rich context
@agent.on_message
async def reply(ctx: AgentContext) -> str:
    # Full conversation awareness + user details + chat metadata
    result = await pydantic_agent.run(ctx.prompt, deps=ctx)
    return result.output
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🐛 Issues

Found a bug or have a feature request? [Open an issue](https://github.com/philmade/gathersdk/issues) on GitHub.

---

**gathersdk v0.0.2**