from run_asr import run_sm_asr
import streamlit as st
import anthropic
from anthropic import AI_PROMPT, HUMAN_PROMPT

anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Client()

def run_completion_and_print():
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response = ""
        for data in client.completions.create(
            prompt=" ".join([m["content"] for m in st.session_state.messages]),
            stop_sequences=[HUMAN_PROMPT],
            model="claude-2",
            max_tokens_to_sample=1000,
            stream=True,
        ):
            response += data.completion
            response_placeholder.markdown(response + "▌")
        response_placeholder.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

st.set_page_config(page_title="Podcast Bot", page_icon="🎙️")
st.title("🎙️ Podcast Bot", anchor=False)
st.markdown("Enter a YouTube link to a podcast to be transcribed and summarized, then ask more questions to clarify!")
link = st.text_input("Enter a YouTube link", placeholder="Enter a YouTube link", label_visibility="hidden")

if link:
    st.video(link)

    if "link" not in st.session_state or link != st.session_state.link:
        # Clear session state
        for key in st.session_state.keys():
            if key != "link":
                del st.session_state[key]
        st.session_state.link = link

    if "transcript" not in st.session_state:
        st.session_state.transcript = run_sm_asr(link)
    with st.expander("Transcript"):
        st.download_button("Download transcript", st.session_state.transcript, "transcript.txt")
        st.write(st.session_state.transcript.replace("$", "\$"))

    just_summarized = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
        summarize_prompt = (
            f"Here's a podcast transcript:\n\n<transcript>{st.session_state.transcript}</transcript>\n\n"
            "Can you give me a summary?"
        )
        st.session_state.messages = [{"role": "user", "content": f"{HUMAN_PROMPT} {summarize_prompt}n\n{AI_PROMPT}"}]
        run_completion_and_print()
        just_summarized = True

    # Display chat messages from history on app rerun
    idx = 2 if just_summarized else 1
    for message in st.session_state.messages[idx:]:
        with st.chat_message(message["role"]):
            content = message["content"]
            if message["role"] == "user":
                content = message["content"][len(f"{HUMAN_PROMPT} ") : -len(f"{AI_PROMPT} ")]
            st.markdown(content)

    # Accept user input
    if prompt := st.chat_input("Ask a question about the podcast"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": f"{HUMAN_PROMPT} {prompt}{AI_PROMPT} "})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        run_completion_and_print()