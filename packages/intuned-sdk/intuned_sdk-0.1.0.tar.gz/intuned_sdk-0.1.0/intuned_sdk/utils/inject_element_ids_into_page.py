from playwright.async_api import Page


async def inject_element_ids_into_page(page: Page):
    await page.evaluate(
        """
        () => {
            // Create a simple hash function for the URL
            const getUrlHash = (str) => {
                let hash = 0;
                for (let i = 0; i < str.length; i++) {
                    const char = str.charCodeAt(i);
                    hash = ((hash << 5) - hash) + char;
                    hash = hash & hash; // Convert to 32-bit integer
                }
                return Math.abs(hash);
            };

            // Seeded random number generator
            const seededRandom = (function() {
                const url = window.location.href;
                let seed = getUrlHash(url);

                return function() {
                    seed = (seed * 16807) % 2147483647;
                    return (seed - 1) / 2147483646;
                };
            })();

            const generateId = () => {
                const chars = 'aA0bB1cC2dD3eE4fF5gG6hH7iI8jJ9kKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ';
                let result = '';
                for (let i = 0; i < 5; i++) {
                    result += chars.charAt(Math.floor(seededRandom() * chars.length));
                }
                return result;
            };

            const usedIds = new Set();

            document.documentElement.querySelectorAll('*').forEach(el => {
                let newId;
                do {
                    newId = generateId();
                } while (usedIds.has(newId));

                usedIds.add(newId);
                el.setAttribute('element_id', newId);
            });
        }
        """
    )
