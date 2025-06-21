document.addEventListener('DOMContentLoaded', function() {
    // Navigation Links
    const watchlistLink = document.getElementById('watchlist-link');

    if (watchlistLink) {
        watchlistLink.addEventListener('click', function() {
            window.location.href = '/watchlist';
        });
    }

    // Stock Cards
    const stockCards = document.querySelectorAll('.stock-card');
    stockCards.forEach(card => {
        card.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            if (url) {
                window.location.href = url;
            }
        });
    });

    // Search Functionality
    const searchBar = document.getElementById('search-bar');
    const searchSuggestionsDiv = document.getElementById('search-suggestions');
    const stockCardsContainer = document.querySelectorAll('.stock-card');
    const industries = document.querySelectorAll('.industry-section');

    searchBar.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        searchSuggestionsDiv.innerHTML = '';
        let hasMatches = false;

        // Search by stock name and industry
        stockCardsContainer.forEach(card => {
            const stockName = card.getAttribute('data-name').toLowerCase();
            const industrySection = card.closest('.industry-section');
            const industryName = industrySection.getAttribute('data-industry').toLowerCase();

            if (stockName.includes(query) || industryName.includes(query)) {
                card.style.display = 'block';
                hasMatches = true;

                // Add suggestion for stock name
                if (stockName.includes(query) && query.length > 0) {
                    const suggestion = document.createElement('div');
                    suggestion.classList.add('suggestion-item');
                    suggestion.textContent = card.getAttribute('data-name');
                    suggestion.addEventListener('click', () => {
                        window.location.href = card.getAttribute('data-url');
                        searchSuggestionsDiv.classList.remove('active');
                    });
                    searchSuggestionsDiv.appendChild(suggestion);
                    searchSuggestionsDiv.classList.add('active');
                }
            } else {
                card.style.display = 'none';
            }
        });

        // Filter industries
        industries.forEach(industry => {
            const industryName = industry.getAttribute('data-industry').toLowerCase();
            const matchingStocks = industry.querySelectorAll('.stock-card:not([style*="display: none"])');
            if (industryName.includes(query) || matchingStocks.length > 0) {
                industry.style.display = 'block';

                // Add suggestion for industry name
                if (industryName.includes(query) && query.length > 0) {
                    const suggestion = document.createElement('div');
                    suggestion.classList.add('suggestion-item');
                    suggestion.textContent = `Industry: ${industryName}`;
                    suggestion.addEventListener('click', () => {
                        searchBar.value = industryName;
                        searchSuggestionsDiv.innerHTML = '';
                        searchSuggestionsDiv.classList.remove('active');
                        industries.forEach(i => i.style.display = i === industry ? 'block' : 'none');
                        stockCardsContainer.forEach(card => {
                            card.style.display = card.closest('.industry-section') === industry ? 'block' : 'none';
                        });
                    });
                    searchSuggestionsDiv.appendChild(suggestion);
                    searchSuggestionsDiv.classList.add('active');
                }
            } else {
                industry.style.display = 'none';
            }
        });

        // Show "No stocks available" message if no matches
        const noStocksMessage = document.getElementById('no-stocks-message');
        if (!hasMatches && query.length > 0) {
            noStocksMessage.style.display = 'block';
            industries.forEach(industry => industry.style.display = 'none');
        } else {
            noStocksMessage.style.display = 'none';
        }

        if (!query) {
            searchSuggestionsDiv.classList.remove('active');
        }
    });

    // Stock Banner Scroll
    const bannerContent = document.getElementById('banner-content');
    if (bannerContent) {
        const bannerItems = bannerContent.innerHTML;
        bannerContent.innerHTML += bannerItems; // Duplicate for seamless scroll
        let scrollAmount = 0;
        const scrollSpeed = 1;

        function scrollBanner() {
            scrollAmount += scrollSpeed;
            if (scrollAmount >= bannerContent.scrollWidth / 2) {
                scrollAmount = 0;
            }
            bannerContent.style.transform = `translateX(-${scrollAmount}px)`;
            requestAnimationFrame(scrollBanner);
        }

        requestAnimationFrame(scrollBanner);
    }

    // Floating Assistant Button Functionality
    const assistantButton = document.getElementById('assistant-button');
    const dialogueBubble = document.getElementById('dialogue-bubble');
    const chatOverlay = document.getElementById('chat-overlay');
    const closeChatButton = document.getElementById('close-chat');
    let hasOpenedChat = false;

    // Debug: Log to confirm elements are found
    console.log('Assistant Button:', assistantButton);
    console.log('Chat Overlay:', chatOverlay);

    if (assistantButton && chatOverlay) {
        // Show dialogue bubble on hover
        assistantButton.addEventListener('mouseenter', () => {
            dialogueBubble.style.display = 'block';
        });

        assistantButton.addEventListener('mouseleave', () => {
            dialogueBubble.style.display = 'none';
        });

        // Toggle chat overlay on click
        assistantButton.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent child elements from interfering
            console.log('Assistant button clicked');
            chatOverlay.classList.toggle('open');
            console.log('Chat overlay open class:', chatOverlay.classList.contains('open')); // Debug
            dialogueBubble.style.display = 'none';

            // Show example queries on first open
            if (!hasOpenedChat) {
                showExampleQueries();
                hasOpenedChat = true;
            }
        });

        // Prevent clicks on the dialogue bubble from affecting the parent
        dialogueBubble.addEventListener('click', (event) => {
            event.stopPropagation();
        });
    } else {
        console.error('Assistant button or chat overlay not found in the DOM');
    }

    if (closeChatButton) {
        closeChatButton.addEventListener('click', () => {
            console.log('Close button clicked');
            chatOverlay.classList.remove('open');
        });
    }

    // Rotate Placeholder Text in Chat Input
    const chatInput = document.getElementById('chat-input');
    const placeholderExamples = [
        "Try: What is the latest price of TATAMOTORS?",
        "Try: What is the volatility of SUZLON?",
        "Try: What is the 5-day moving average of TCS?",
        "Try: Which stock has the best trend?",
        "Try: What is the volume of INFY?"
    ];
    let currentPlaceholderIndex = 0;

    function rotatePlaceholder() {
        chatInput.placeholder = placeholderExamples[currentPlaceholderIndex];
        currentPlaceholderIndex = (currentPlaceholderIndex + 1) % placeholderExamples.length;
    }

    // Rotate placeholder every 5 seconds
    rotatePlaceholder(); // Set initial placeholder
    setInterval(rotatePlaceholder, 5000);

    // Chat Functionality
    window.sendMessage = function() {
        const input = document.getElementById('chat-input');
        const chatBox = document.getElementById('chat-box');
        const message = input.value.trim();

        if (!message) return;

        // Display user message
        const userDiv = document.createElement('div');
        userDiv.className = 'chat-message user-message';
        userDiv.textContent = 'You: ' + message;
        chatBox.appendChild(userDiv);

        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading-indicator';
        loadingDiv.className = 'chat-message assistant-message';
        loadingDiv.innerHTML = '<div class="typing-dots"><span>.</span><span>.</span><span>.</span></div>';
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Send message to the server
        fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            loadingDiv.remove();

            // Display assistant response
            const assistantDiv = document.createElement('div');
            assistantDiv.className = 'chat-message assistant-message';
            assistantDiv.textContent = 'Assistant: ' + data.response;
            chatBox.appendChild(assistantDiv);

            // Scroll to the bottom of the chat box
            chatBox.scrollTop = chatBox.scrollHeight;

            // Clear input and hide suggestions
            input.value = '';
            const chatSuggestionsDiv = document.getElementById('chat-suggestions');
            chatSuggestionsDiv.classList.remove('active');
        })
        .catch(error => {
            // Remove loading indicator
            loadingDiv.remove();

            console.error('Error:', error);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'chat-message assistant-message';
            errorDiv.textContent = 'Assistant: Error communicating with the server.';
            chatBox.appendChild(errorDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    };

    // Function to show example queries in the chat box
    window.showExampleQueries = function() {
        const chatBox = document.getElementById('chat-box');
        const examplesDiv = document.createElement('div');
        examplesDiv.className = 'chat-message assistant-message';
        examplesDiv.innerHTML = `
            <strong>Assistant:</strong> Here are some things you can ask me about stocks:<br>
            - What is the latest price of TATAMOTORS?<br>
            - What is the 52-week high of INFY?<br>
            - What is the volatility of SUZLON?<br>
            - What is the 5-day moving average of TCS?<br>
            - What is the volume of WIPRO?<br>
            - What is the daily price change of HCLTECH?<br>
            - Which stock has the best trend?<br>
            - Which stock has the highest volume?<br>
            - Which stock has the highest volatility?<br>
            Type any question to get started, or try one of these!
        `;
        chatBox.appendChild(examplesDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Hide suggestions after clicking "Discover what I can do..."
        const chatSuggestionsDiv = document.getElementById('chat-suggestions');
        chatSuggestionsDiv.classList.remove('active');
    };

    // Chat Suggestions with "Discover More" Option
    window.fetchChatSuggestions = function(partialInput) {
        const chatSuggestionsDiv = document.getElementById('chat-suggestions');
        console.log('Fetching suggestions for:', partialInput);

        // Show "Discover what I can do..." when input is empty or generic
        const trimmedInput = partialInput.trim().toLowerCase();
        const showDiscoverOption = !trimmedInput || trimmedInput === 'what' || trimmedInput === 'what is';

        if (!trimmedInput && !showDiscoverOption) {
            console.log('Input is empty and no discover option needed, hiding suggestions');
            chatSuggestionsDiv.classList.remove('active');
            chatSuggestionsDiv.innerHTML = '';
            return;
        }

        // If showing the discover option, add it immediately
        if (showDiscoverOption) {
            chatSuggestionsDiv.innerHTML = '';
            const discoverDiv = document.createElement('div');
            discoverDiv.classList.add('suggestion-item', 'discover-option');
            discoverDiv.textContent = 'Discover what I can do...';
            discoverDiv.addEventListener('click', showExampleQueries);
            chatSuggestionsDiv.appendChild(discoverDiv);
            chatSuggestionsDiv.classList.add('active');

            // If input is empty, we can stop here
            if (!trimmedInput) {
                console.log('Showing only "Discover what I can do..." for empty input');
                return;
            }
        }

        // Proceed with fetching suggestions for non-empty input
        const url = 'http://localhost:5000/chat_suggestions';
        console.log('Sending fetch request to:', url);
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ partial_input: partialInput }),
            mode: 'cors'
        })
        .then(response => {
            console.log('Fetch response status:', response.status);
            console.log('Fetch response headers:', response.headers.get('content-type'));
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Suggestions received:', data);
            let suggestions = data.suggestions || [];

            // If showing the discover option, ensure it's at the top
            if (showDiscoverOption) {
                const discoverDiv = document.createElement('div');
                discoverDiv.classList.add('suggestion-item', 'discover-option');
                discoverDiv.textContent = 'Discover what I can do...';
                discoverDiv.addEventListener('click', showExampleQueries);
                chatSuggestionsDiv.innerHTML = '';
                chatSuggestionsDiv.appendChild(discoverDiv);
            } else {
                chatSuggestionsDiv.innerHTML = '';
            }

            // Add the fetched suggestions
            if (suggestions.length > 0) {
                suggestions.forEach(suggestion => {
                    const suggestionDiv = document.createElement('div');
                    suggestionDiv.classList.add('suggestion-item');
                    suggestionDiv.textContent = suggestion;
                    suggestionDiv.addEventListener('click', () => {
                        document.getElementById('chat-input').value = suggestion;
                        chatSuggestionsDiv.classList.remove('active');
                        sendMessage();
                    });
                    chatSuggestionsDiv.appendChild(suggestionDiv);
                });
                console.log('Showing suggestions dropdown with', suggestions.length + (showDiscoverOption ? 1 : 0), 'items');
                chatSuggestionsDiv.classList.add('active');
            } else if (showDiscoverOption) {
                console.log('No additional suggestions, but showing "Discover what I can do..."');
                chatSuggestionsDiv.classList.add('active');
            } else {
                console.log('No suggestions to show, hiding dropdown');
                chatSuggestionsDiv.classList.remove('active');
            }
        })
        .catch(error => {
            console.error('Error fetching chat suggestions:', error.message);
            console.log('Full error object:', error);
            const chatBox = document.getElementById('chat-box');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'chat-message assistant-message';
            errorDiv.textContent = 'Assistant: Failed to load suggestions. Please try again.';
            chatBox.appendChild(errorDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
            chatSuggestionsDiv.classList.remove('active');
        });
    };

    // Handle keyboard navigation for chat suggestions
    window.handleChatInput = function(event) {
        const chatSuggestionsDiv = document.getElementById('chat-suggestions');
        const input = document.getElementById('chat-input');
        const suggestions = chatSuggestionsDiv.querySelectorAll('.suggestion-item');
        let selectedIndex = -1;

        // Find the currently selected suggestion
        suggestions.forEach((suggestion, index) => {
            if (suggestion.classList.contains('selected')) {
                selectedIndex = index;
            }
        });

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            if (selectedIndex < suggestions.length - 1) {
                if (selectedIndex >= 0) {
                    suggestions[selectedIndex].classList.remove('selected');
                }
                selectedIndex++;
                suggestions[selectedIndex].classList.add('selected');
                suggestions[selectedIndex].scrollIntoView({ block: 'nearest' });
            }
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            if (selectedIndex > 0) {
                suggestions[selectedIndex].classList.remove('selected');
                selectedIndex--;
                suggestions[selectedIndex].classList.add('selected');
                suggestions[selectedIndex].scrollIntoView({ block: 'nearest' });
            }
        } else if (event.key === 'Enter') {
            if (selectedIndex >= 0) {
                event.preventDefault();
                const selectedSuggestion = suggestions[selectedIndex];
                if (selectedSuggestion.classList.contains('discover-option')) {
                    showExampleQueries();
                } else {
                    input.value = selectedSuggestion.textContent;
                    chatSuggestionsDiv.classList.remove('active');
                    sendMessage();
                }
            } else if (input.value.trim()) {
                sendMessage();
            }
        } else if (event.key === 'Escape') {
            chatSuggestionsDiv.classList.remove('active');
        }
    };

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        const chatSuggestionsDiv = document.getElementById('chat-suggestions');
        const chatInput = document.getElementById('chat-input');
        const searchSuggestionsDiv = document.getElementById('search-suggestions');
        const searchBar = document.getElementById('search-bar');

        if (!chatSuggestionsDiv.contains(e.target) && e.target !== chatInput) {
            chatSuggestionsDiv.classList.remove('active');
        }
        if (!searchSuggestionsDiv.contains(e.target) && e.target !== searchBar) {
            searchSuggestionsDiv.classList.remove('active');
        }
    });
});