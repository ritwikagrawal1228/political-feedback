document.addEventListener('DOMContentLoaded', () => {
    const campaignId = document.body.dataset.campaignId;
    if (!campaignId) {
        console.error('No Campaign ID found on body tag!');
        return;
    }

    const state = {
        current: 'initial',
        topic: null,
        conversation: [],
    };

    const initialScreen = document.getElementById('initial-screen');
    const chatScreen = document.getElementById('chat-screen');
    const topicCards = document.querySelectorAll('.topic-card');

    let messagesContainer, input, sendButton, voiceButton, chatInputContainer;

    function renderChatScreen() {
        initialScreen.classList.add('d-none');
        chatScreen.classList.remove('d-none');
        chatScreen.innerHTML = `
            <div class="chat-container">
                <div class="chat-header">
                    <h3>Chat with Eli</h3>
                </div>
                <div class="chat-messages"></div>
                <div class="chat-input">
                    <input type="text" class="form-control" placeholder="Write Something...">
                    <button class="btn btn-outline-secondary" id="voice-btn" title="Use voice input">🎤</button>
                    <button class="btn btn-primary">Send</button>
                </div>
            </div>
        `;

        messagesContainer = chatScreen.querySelector('.chat-messages');
        input = chatScreen.querySelector('input');
        sendButton = chatScreen.querySelector('button.btn-primary');
        voiceButton = chatScreen.querySelector('#voice-btn');
        chatInputContainer = chatScreen.querySelector('.chat-input');

        sendButton.addEventListener('click', () => processInput());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') processInput();
        });
        voiceButton.addEventListener('click', () => showCallout('Voice Input is not implemented yet.'));
    }

    function addMessage(text, from) {
        const message = document.createElement('div');
        message.className = `message ${from}-message`;
        message.textContent = text;
        messagesContainer.appendChild(message);
        state.conversation.push({ from: from, text: text });
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function addTopicSelection(topicName) {
        const topicGridContainer = document.createElement('div');
        topicGridContainer.className = 'topic-grid-container in-chat';
        const topicGrid = document.createElement('div');
        topicGrid.className = 'topic-grid';
        
        // Clone topic cards from initial screen to maintain consistency
        const originalTopicCards = document.querySelectorAll('#initial-screen .topic-card');
        originalTopicCards.forEach(originalCard => {
            const newCard = originalCard.cloneNode(true);
            newCard.addEventListener('click', () => {
                state.current = 'q3_answered';
                addMessage(newCard.dataset.topic, 'user');
                topicGridContainer.remove();
                setTimeout(runStateMachine, 500);
            });
            topicGrid.appendChild(newCard);
        });

        topicGridContainer.appendChild(topicGrid);
        messagesContainer.appendChild(topicGridContainer);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function saveChatToDB() {
        console.log("Saving conversation...", state.conversation);
        try {
            const response = await fetch('/api/save_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    campaign_id: campaignId,
                    initial_topic: state.topic,
                    conversation: state.conversation
                }),
            });
            const data = await response.json();
            if (data.status !== 'success') {
                console.error('Failed to save chat:', data.message);
            } else {
                console.log('Chat saved successfully.');
            }
        } catch (error) {
            console.error('Error saving chat:', error);
        }
    }

    function runStateMachine() {
        console.log(`State: ${state.current}`);
        // This function now just handles ELI's actions
        switch (state.current) {
            case 'topic_selected':
                addMessage(`I see you chose ${state.topic}, what's behind that for you?`, 'eli');
                input.disabled = false;
                sendButton.disabled = false;
                input.focus();
                state.current = 'q1_asked';
                break;
            case 'q1_answered':
                addMessage(`What specific opinion do you have for ${state.topic}? Feel free to be blunt, we support free speech OR you can skip this.`, 'eli');
                addSkipButton('q2_skipped');
                input.disabled = false;
                sendButton.disabled = false;
                input.focus();
                state.current = 'q2_asked';
                break;
            case 'q2_answered': // covers both skipped and answered
                addMessage('Got it, thanks! Are there other issues of near or equal importance to you right now?', 'eli');
                addTopicSelection();
                input.disabled = true;
                sendButton.disabled = true;
                state.current = 'q3_asked';
                break;
            case 'q3_answered':
                 addMessage('Feel free to express your opinion here, this is a free speech space. You can skip this as well.', 'eli');
                addSkipButton('q4_skipped');
                input.disabled = false;
                sendButton.disabled = false;
                input.focus();
                state.current = 'q4_asked';
                break;
            case 'q4_answered': // covers both skipped and answered
                addMessage('Thank you for your feedback!', 'eli');
                input.disabled = true;
                sendButton.disabled = true;
                saveChatToDB();
                state.current = 'done';
                break;
        }
    }

    function processInput() {
        // This function handles the USER'S actions
        const userInput = input.value.trim();
        if (userInput === '') return;

        switch (state.current) {
            case 'q1_asked':
                state.current = 'q1_answered';
                addMessage(userInput, 'user');
                input.value = '';
                input.disabled = true;
                sendButton.disabled = true;
                setTimeout(runStateMachine, 500);
                break;
            case 'q2_asked':
                state.current = 'q2_answered';
                removeSkipButton();
                addMessage(userInput, 'user');
                input.value = '';
                input.disabled = true;
                sendButton.disabled = true;
                setTimeout(runStateMachine, 500);
                break;
            case 'q4_asked':
                 state.current = 'q4_answered';
                removeSkipButton();
                addMessage(userInput, 'user');
                input.value = '';
                input.disabled = true;
                sendButton.disabled = true;
                setTimeout(runStateMachine, 500);
                break;
        }
    }
    
    function addSkipButton(targetState) {
        const skipButton = document.createElement('button');
        skipButton.id = 'skip-btn';
        skipButton.className = 'btn btn-secondary ms-2';
        skipButton.textContent = 'Skip';
        skipButton.onclick = () => {
            state.current = targetState;
            addMessage('(Skipped)', 'user');
            removeSkipButton();
            input.disabled = true;
            sendButton.disabled = true;
            setTimeout(runStateMachine, 500);
        };
        chatInputContainer.appendChild(skipButton);
    }
    
    function removeSkipButton(){
        const skipButton = document.getElementById('skip-btn');
        if(skipButton) skipButton.remove();
    }

    topicCards.forEach(card => {
        card.addEventListener('click', () => {
            state.topic = card.dataset.topic;
            state.current = 'topic_selected';
            renderChatScreen();
            runStateMachine();
        });
    });

    function showCallout(message) {
        const callout = document.createElement('div');
        callout.className = 'chat-callout';
        callout.textContent = message;
        
        document.body.appendChild(callout);

        setTimeout(() => {
            callout.classList.add('show');
        }, 10);

        setTimeout(() => {
            callout.classList.remove('show');
            setTimeout(() => {
                callout.remove();
            }, 300);
        }, 2500);
    }
}); 