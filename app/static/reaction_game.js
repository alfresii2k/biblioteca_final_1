// Inicializa el juego solo en páginas que tengan el tablero de memoria.
document.addEventListener('DOMContentLoaded', () => {
    const board = document.getElementById('memoryBoard');
    if (!board) return;

    const books = JSON.parse(document.getElementById('memoryBooksData').textContent || '[]');
    const movesElement = document.getElementById('memoryMoves');
    const timeElement = document.getElementById('memoryTime');
    const pairsElement = document.getElementById('memoryPairs');
    const totalPairsElement = document.getElementById('memoryTotalPairs');
    const messageElement = document.getElementById('memoryMessage');
    const levels = { easy: 4, medium: 6, hard: 8 };
    // Estado compartido entre el tablero, el cronómetro y los controles.
    let level = 'easy';
    let cards = [];
    let openCards = [];
    let moves = 0;
    let pairs = 0;
    let seconds = 0;
    let timer = null;
    let locked = false;
    let gameStarted = false;

    // Devuelve una copia mezclada para no reordenar la lista original.
    function shuffle(items) {
        return [...items].sort(() => Math.random() - 0.5);
    }

    // Repite los libros disponibles si el nivel requiere más pares que títulos.
    function sourceBooks(pairCount) {
        const available = books.length ? books : [{ titulo: 'El Principito', autor: 'Antoine de Saint-Exupéry' }];
        return Array.from({ length: pairCount }, (_, index) => available[index % available.length]);
    }

    // Reinicia el contador y actualiza el tiempo transcurrido cada segundo.
    function startTimer() {
        clearInterval(timer);
        seconds = 0;
        timer = setInterval(() => {
            seconds += 1;
            timeElement.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
        }, 1000);
    }

    // Crea una carta accesible como botón y conecta su evento de selección.
    function createCard(card, index) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'memory-card';
        button.dataset.index = index;
        button.innerHTML = `<span class="memory-card-back"><i class="fas fa-book-open"></i></span><span class="memory-card-face"><small>${card.type === 'title' ? 'LIBRO' : 'AUTOR'}</small><strong>${card.value}</strong></span>`;
        button.addEventListener('click', () => revealCard(button, index));
        return button;
    }

    // Genera los pares del nivel actual y reinicia el estado de la partida.
    function renderBoard() {
        const pairCount = levels[level];
        const chosenBooks = sourceBooks(pairCount);
        cards = shuffle(chosenBooks.flatMap((book, index) => [
            { match: index, type: 'title', value: book.titulo },
            { match: index, type: 'author', value: book.autor }
        ]));
        board.className = `memory-board board-${level}`;
        board.replaceChildren(...cards.map(createCard));
        moves = 0;
        pairs = 0;
        openCards = [];
        locked = false;
        gameStarted = false;
        clearInterval(timer);
        movesElement.textContent = '0';
        pairsElement.textContent = '0';
        totalPairsElement.textContent = pairCount;
        timeElement.textContent = '00:00';
        messageElement.textContent = 'Encuentra las parejas para completar el desafío.';
    }

    // Revela una carta y compara cada pareja; bloquea el tablero al ocultar fallos.
    function revealCard(button, index) {
        if (locked || openCards.includes(index) || cards[index].matched) return;
        if (!gameStarted) {
            gameStarted = true;
            startTimer();
            messageElement.textContent = 'El tiempo corre. Encuentra todas las parejas.';
        }
        button.classList.add('flipped');
        openCards.push(index);
        if (openCards.length < 2) return;

        moves += 1;
        movesElement.textContent = moves;
        const [first, second] = openCards;
        if (cards[first].match === cards[second].match && cards[first].type !== cards[second].type) {
            cards[first].matched = true;
            cards[second].matched = true;
            board.children[first].classList.add('matched');
            board.children[second].classList.add('matched');
            pairs += 1;
            pairsElement.textContent = pairs;
            openCards = [];
            if (pairs === levels[level]) {
                clearInterval(timer);
                messageElement.textContent = `¡Excelente! Completaste el nivel en ${moves} movimientos.`;
            }
            return;
        }

        locked = true;
        setTimeout(() => {
            board.children[first].classList.remove('flipped');
            board.children[second].classList.remove('flipped');
            openCards = [];
            locked = false;
        }, 750);
    }

    // Cambiar dificultad o reiniciar genera una partida limpia.
    document.querySelectorAll('.memory-level').forEach((button) => {
        button.addEventListener('click', () => {
            document.querySelector('.memory-level.active').classList.remove('active');
            button.classList.add('active');
            level = button.dataset.level;
            renderBoard();
        });
    });
    document.getElementById('memoryReset').addEventListener('click', renderBoard);
    renderBoard();
});
