import streamlit as st
import request

st.title("LLM response analyzer")

prompt = st.text_area("Enter prompt: ")

if st.button("Run"):
    if not prompt.strip():
        st.warning("Enter a prompt before running the model.")
    else:
        try:
            output, latency, cost = request.call_gemma(prompt)
            st.subheader("Gemma")
            st.write(f"Latency: {latency:.2f}s")
            st.write(f"Cost: ${cost:.6f}")
            st.write(output)
        except Exception as exc:
            st.error(f"Request failed: {exc}")
import streamlit as st
import request

st.title("LLM response analyzer")

prompt = st.text_area("Enter prompt: ")

if st.button("Run"):
    if not prompt.strip():
        st.warning("Enter a prompt before running the model.")
    else:
        try:
            output, latency, cost = request.call_gemma(prompt)
            st.subheader("Gemma")
            st.write(f"Latency: {latency:.2f}s")
            st.write(f"Cost: ${cost:.6f}")
            st.write(output)
        except Exception as exc:
            st.error(f"Request failed: {exc}")