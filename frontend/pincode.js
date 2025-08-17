
$(document).ready(function() {
    function getRandomDigit() {
        return Math.floor(Math.random() * 10);
    }

    function generateRandomDigits() {
        let randomDigits = '';
        for (let i = 0; i < 4; i++) {
            randomDigits += getRandomDigit();
        }
        pinCode = randomDigits;
    }

    function animatePinCode() {
        let interval = setInterval(function() {
            generateRandomDigits();
            $('#pinCode').text(pinCode);
            console.log('Последнее значение пинкода:', pinCode);
        }, 100); // Каждую десятую долю секунды

        setTimeout(function() {
            clearInterval(interval);
        }, 1000); // Останавливаем через 1 секунду
    }
    
    $('#refreshPin').click(function() {
        animatePinCode()
    });

    generateRandomDigits()
    $('#pinCode').text(pinCode);
    
    setTimeout(()=>{$('#usePin').prop('checked', false)},0)
});
