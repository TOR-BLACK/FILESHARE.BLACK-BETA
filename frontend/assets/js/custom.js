let links = document.querySelectorAll('.air-header__link');
let width = window.innerWidth;
let nav = document.querySelector('.air-header__nav ml10_ df');

function handleLinkClick(event) {
    event.preventDefault();

    for (let i = 0; i < links.length; i++) {
        links[i].classList.remove('active');
    }
    nav.classList.toggle('active');
    this.classList.add('active');
}

function handleWindowResize() {
    width = window.innerWidth;

    if (width <= 992) {
        for (let i = 0; i < links.length; i++) {
            links[i].addEventListener('click', handleLinkClick);
        }
    } else {
        for (let i = 0; i < links.length; i++) {
            links[i].addEventListener('click', handleLinkClick);
        }
    }
}

window.addEventListener('resize', handleWindowResize);
handleWindowResize();


const copyButton = document.querySelector('.air-download-link__copy');
const linkUrl = document.querySelector('.air-download-link__url');

// Проверяем что copyButton и linkUrl существуют на странице
if (copyButton && linkUrl) {
    copyButton.addEventListener('click', (event) => {
        if (copyButton.classList.contains('active')) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        linkUrl.classList.add('active');
        setTimeout(() => {
            linkUrl.classList.remove('active');
        }, 200);

        navigator.clipboard.writeText(linkUrl.textContent)
            .then(() => {
                copyButton.textContent = 'Скопировано!';
                copyButton.classList.add('active');
                setTimeout(() => {
                    copyButton.textContent = 'Скопировать';
                    copyButton.classList.remove('active');
                }, 2000);
            })
            .catch((err) => {
                console.error('Не удалось скопировать текст:', err);
            });
    });
}


var element_glide = document.getElementById('slider-single');

if (element_glide) {
    var element_gl = new Glide('#slider-single', {

        type: 'slider',
        perView: 1,
        autoplay: false,
        hoverpause: true,
        animationTimingFunc: 'cubic-bezier(0.165, 0.840, 0.440, 1.000)',
        animationDuration: 400,
        arrows: false,
        gap: 0
    });

    element_gl.mount();

    element_gl.on(['run.after'], function () {
        var currentSlide = element_gl.index;
        // находим элемент с классом "air-bread__count" и устанавливаем номер текущего слайда
        var counterElement = document.querySelector('.air-bread__count');
        if(counterElement) {
            counterElement.textContent = currentSlide + 1; // +1 т.к. индексация слайдов с 0
        }

        setTimeout(function() {
            var activeSlide = document.querySelector('.glide__slide--active');

            if(activeSlide) {
                var title = activeSlide.getAttribute('data-title');
                var link = activeSlide.getAttribute('data-link');

                var day = activeSlide.getAttribute('data-day');
                var size = activeSlide.getAttribute('data-size');
                var views = activeSlide.getAttribute('data-views');
                var downloads = activeSlide.getAttribute('data-downloads');
            }
        }, 100);

    });

}

var closeButton = document.querySelector('.air-mobile-close');
var cartElement = document.querySelector('.air-cart__right');

if (closeButton && cartElement) {
    closeButton.addEventListener('click', function() {
        cartElement.classList.remove('open');
    });
}

/*
 * Анимация набора текста
 */

var animationTimeout;

// Функция для анимации текста
function typeText(textElement, text) {
    var index = 0;
    var htmlText = '';

    function animate() {
        if (index < text.length) {
            htmlText += text.charAt(index);
            textElement.innerHTML = htmlText;
            index++;
            animationTimeout = setTimeout(animate, 13);
        }
    }

    animate();
}

// Функция для остановки текущей анимации
function stopAnimation() {
    clearTimeout(animationTimeout);
}

/*
 * Видео
 */
const videoContainers = document.querySelectorAll('.air-video-container');

videoContainers.forEach(container => {
    const videoPlayer = container.querySelector('.air-video-player');
    const playButton = container.querySelector('.air-play-button');

    playButton.addEventListener('click', function() {
        if (videoPlayer.paused) {
            videoPlayer.play();
            this.style.visibility = 'hidden';
            videoPlayer.controls = true;
            videoPlayer.classList.add('show');
        } else {
            videoPlayer.pause();
        }
    });

    videoPlayer.addEventListener('pause', function() {
        playButton.style.visibility = 'visible';
        this.controls = false;
        videoPlayer.classList.remove('show');
    });

    videoPlayer.addEventListener('play', function() {
        playButton.style.visibility = 'hidden';
        this.controls = true;
    });
});