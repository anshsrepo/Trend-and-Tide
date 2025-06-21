document.addEventListener('DOMContentLoaded', async () => {
    // Navigation Links
    const homeLink = document.getElementById('home-link');
    const watchlistLink = document.getElementById('watchlist-link');

    if (homeLink) {
        homeLink.addEventListener('click', () => {
            window.location.href = '/';
        });
    }

    if (watchlistLink) {
        watchlistLink.addEventListener('click', () => {
            window.location.href = '/watchlist';
        });
    }

    // Plot Toggle Buttons
    const linePlotBtn = document.getElementById('line-plot-btn');
    const candlestickChartBtn = document.getElementById('candlestick-chart-btn');

    if (linePlotBtn) {
        const stockName = linePlotBtn.getAttribute('data-stock-name');
        linePlotBtn.addEventListener('click', () => {
            window.location.href = `/stock/${stockName}?plot_type=line`;
        });
    }

    if (candlestickChartBtn) {
        const stockName = candlestickChartBtn.getAttribute('data-stock-name');
        candlestickChartBtn.addEventListener('click', () => {
            window.location.href = `/stock/${stockName}?plot_type=candlestick`;
        });
    }

    // Watchlist Functionality
    const watchlistBtn = document.getElementById('watchlist-btn');

    // Get stock name from the DOM
    const stockNameElement = document.querySelector('.stock-details-card h2');
    const stockName = stockNameElement ? stockNameElement.textContent : null;
    const stockId = stockName; // Using stock name as ID for consistency with server

    if (watchlistBtn && stockId) {
        let isInWatchlist = false;

        // Fetch the current watchlist to determine if the stock is already in it
        try {
            const response = await fetch('/watchlist');
            const html = await response.text();
            // Parse the HTML to check if the stock is in the watchlist
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const watchlistItems = doc.querySelectorAll('.watchlist-table-row .watchlist-table-cell a');
            isInWatchlist = Array.from(watchlistItems).some(item => item.textContent === stockId);
        } catch (error) {
            console.error('Error fetching watchlist:', error);
            alert('An error occurred while checking the watchlist. Please try again.');
        }

        // Update button state
        const updateButton = () => {
            watchlistBtn.textContent = isInWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist';
            watchlistBtn.className = `button ${isInWatchlist ? 'button-added' : ''}`;
        };

        updateButton();

        // Handle watchlist button click
        watchlistBtn.addEventListener('click', async () => {
            const endpoint = isInWatchlist ? '/remove_from_watchlist' : '/add_to_watchlist';
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ stock_name: stockId }),
                });

                const result = await response.json();
                if (result.success) {
                    isInWatchlist = !isInWatchlist;
                    updateButton();
                } else {
                    console.error(`Failed to ${isInWatchlist ? 'remove' : 'add'} stock:`, result.message);
                    alert(`Error: ${result.message}`);
                }
            } catch (error) {
                console.error(`Error ${isInWatchlist ? 'removing' : 'adding'} stock to watchlist:`, error);
                alert(`An error occurred while ${isInWatchlist ? 'removing' : 'adding'} the stock. Please try again.`);
            }
        });
    }
});