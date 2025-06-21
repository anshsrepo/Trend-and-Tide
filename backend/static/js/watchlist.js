document.addEventListener('DOMContentLoaded', () => {
    const watchlistContainer = document.getElementById('watchlist-container');
    const watchlistMessage = document.getElementById('watchlist-message');

    // Attach event listeners to all "Remove" buttons
    const attachRemoveListeners = () => {
        const removeButtons = document.querySelectorAll('.remove-button');
        removeButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const stockName = button.getAttribute('data-stock-name');
                if (!stockName) {
                    console.error('No stock name found for removal');
                    return;
                }

                try {
                    const response = await fetch('/remove_from_watchlist', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ stock_name: stockName }),
                    });

                    const result = await response.json();
                    if (result.success) {
                        // Refresh the page to reflect the updated watchlist
                        window.location.reload();
                    } else {
                        console.error('Failed to remove stock:', result.message);
                        alert(`Error: ${result.message}`);
                    }
                } catch (error) {
                    console.error('Error removing stock from watchlist:', error);
                    alert('An error occurred while removing the stock. Please try again.');
                }
            });
        });
    };

    // Initial setup: attach listeners to existing buttons
    if (watchlistContainer) {
        attachRemoveListeners();
    }

    // Update the message if the watchlist is empty
    if (watchlistContainer && watchlistContainer.children.length === 0) {
        watchlistMessage.textContent = 'Your watchlist is empty. Add stocks to start tracking!';
    }
});