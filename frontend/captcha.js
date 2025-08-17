const canvas = document.getElementById('captcha');
const context = canvas.getContext('2d');
const captchaInput = document.getElementById('captchaInput');
const message = document.getElementById('message');

let captchaText;


function generateCaptcha() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    captchaText = '';  // Название переменной должно быть с `let` или `const`
    for (let i = 0; i < 5; i++) {
        captchaText += chars.charAt(Math.floor(Math.random() * chars.length));
    }

    context.clearRect(0, 0, canvas.width, 200);
    context.fillStyle = '#161616';
    context.fillRect(0, 0, canvas.width, 200);
    
    // Параметры для отрисовки текста
    context.fillStyle = 'white';
    context.font = '96px VENOM';
    
    let x = 25; // Начальная позиция по оси X
    for (let i = 0; i < captchaText.length; i++) {
        // Генерируем случайный угол наклона от -45 до 45 градусов
        
        // Сохраняем текущее состояние контекста
        context.save();
        
        // Перемещаем контекст в нужную позицию
        context.translate(x, 140); // перемещаем на позицию по X и Y
        
        // Отрисовываем символ
        context.fillText(captchaText[i], 0, 0);
        context.textAlign = "center";
        
        // Восстанавливаем предыдущее состояние контекста
        context.restore();
        
        // Увеличиваем позицию по оси X для следующего символа
        x += 50; // можно настроить, чтобы символы размещались по вашему желанию
    }
}

// Вызов функции генерации капчи
let f = new FontFace("VENOM", "url(/assets/fonts/VENOM.ttf)");

f.load().then(function (loadedFont) {
    // Добавляем шрифт в документ
    document.fonts.add(loadedFont);
    // Генерируем капчу после загрузки шрифта
    generateCaptcha();
}).catch(function (error) {
    console.error('Ошибка загрузки шрифта:', error);
});

function checkoutCaptcha () {
    if (captchaInput.value === captchaText) {
        message.textContent = 'Капча пройдена!';
        $('#captchaBg').fadeOut();
        message.textContent = '';
        setCookie('captcha', 'valid', 30)
    } else {
        message.textContent = 'Неверная капча, попробуйте снова.';
        message.textContent = '';
    }
        generateCaptcha(); // Генерируем новую капчу
        captchaInput.value = ''; // Очищаем входное поле
}

// Обработка события нажатия кнопки
document.getElementById('submitBtn').addEventListener('click', checkoutCaptcha);

$(document).on('keydown', function(event) {
    console.log(fileQueue.length)
    if (event.key === 'Enter' && !$('#description').is(':focus')) {
        if ($('#captchaBg').is(':visible')) {
            checkoutCaptcha();
        } else if ($('#captchaBg').is(':hidden') && $('.air-file__container').is(':visible')){
            if(fileQueue.length === 0){
                alert('Добавьте файлы для загрузки')
            }else{
                sendFiles()
            }
        }
    }
});

// Перегенерация капчи при клике на холст
canvas.addEventListener('click', generateCaptcha);

function captchaToUpper(element) {
    element.value = element.value.toUpperCase();
}