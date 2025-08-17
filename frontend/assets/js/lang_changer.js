function isRus() {
    return lang == 1;
}

function setLang(lang_id) {
    setCookie("lang_id", lang_id);
    lang = lang_id;
    if (isRus()) {
        $('#lang1').addClass("active mb-dn");
        $('#lang2').removeClass("active mb-dn");
        $('#text1').text("Главная страница");
        $('#text2').text("Загружай файлы");
        $('#add-button').text("Добавить файлы");
        $('#text3').html("для вставки файлов, из&nbsp;буфера обмена, нажмите CTRL+V");
        $('#text4').text("до окончания загрузки");
        $('#text6').text("общий размер");
        $('#text7').text("6 месяцев");
        $('#text8').text("1 год");
        $('#text9').text("Бессрочно");
        $('#text10-1').text("Управление загруженными файлами:");
        $('#text10').text("Скачать в архиве:");
        $('#text10-2').text("Ваша ссылка для удаления:");
        $('.air-download-link__copy').text("Скопировать");
        $('#descrOnText').text("Добавить комментарий");
        $('#uploadMoreComment').text("Нужно загрузить еще файл? Нажмите еще раз!");
        $('#addPin').text("Добавить пинкод");
        $('.slider-option:nth-child(1)').text("1 день");
        $('.slider-option:nth-child(2)').text("3 дня");
        $('.slider-option:nth-child(3)').text("неделя");
        $('.slider-option:nth-child(4)').text("месяц");
        $('.slider-option:nth-child(5)').text("3 месяца");
        $('#dragImage div').text("Перетащите файл");
        $('#enterToSend').text("Чтобы отправить файл нажмите Enter");
        $('#commentNumericOnText').text("Показать нумерацию");
        $('#sliderOptionDisabled').text("бессрочно");
        $('#saveLinkLabel').text("Безопасная ссылка");
        $('#prepareFilesDeleteComment').text("Файлы удалены.");
        $('#usePinLabel').text("Добавить пинкод");
        $('#text10-each').text("Ссылки на файлы:");
        $('label[for="upload-pin"]').text("Пин-код");
        $('#upload-pin').attr("placeholder", "Введите пин-код");
        $('.air-file__code-faq-text').text("Доступ к бессрочной загрузке могут получить лица, знающие пин-код. Пин-код можно узнать у администрации данного ресурса.");
        $('.air-file__code-error').text("Вы ввели неверный пин-код");
        $('.air-file__compression-label').text("Сжатие файлов");
        $('.air-file__compression-toggle-text').text(isCompressionEnabled ? 'Вкл' : "Выкл");
        if (isLoadFinishined) {
            $('#progress_text').text("ЗАГРУЖЕНО");
        }
        $('#deletePopupDeleteBtn').val("Удалить");
        $('#deletePopupCancelBtn').val("Отмена");
        $('#deletePopup h2').text("Вы точно хотите удалить загруженные файлы");
        $('.send_files_text').text("Отправить");
        $('#submitBtn').text("Отправить");
    }
    else if (lang_id == 2) {
        $('#lang2').addClass("active mb-dn");
        $('#lang1').removeClass("active mb-dn");
        $('#text1').text("Home page");
        $('#text2').text("Upload files");
        $('#add-button').text("Add files");
        $('#text3').text("to insert file, from clipboard, click CTRL+V");
        $('#text4').text("until download finishes");
        $('#text6').text("overall size");
        $('#text7').text("6 months");
        $('#text8').text("1 year");
        $('#text9').text("indefinitely");
        $('#text10-1').text("Managing uploaded files:");
        $('#text10').text("Archived download:");
        $('#text10-2').text("Your link to delete:");
        $('.air-download-link__copy').text("Copy");
        $('#descrOnText').text("Add comment");
        $('#uploadMoreComment').text("Do I need to upload another file? Click again!");
        $('#addPin').text("Add pin-code");
        $('.slider-option:nth-child(1)').text("1 day");
        $('.slider-option:nth-child(2)').text("3 days");
        $('.slider-option:nth-child(3)').text("week");
        $('.slider-option:nth-child(4)').text("month");
        $('.slider-option:nth-child(5)').text("3 months");
        $('#dragImage div').text("Drop the file");
        $('#enterToSend').text("To send the file, press Enter");
        $('#commentNumericOnText').text("Show the numbering");
        $('#sliderOptionDisabled').text("unlimited");
        $('#saveLinkLabel').text("Safe link");
        $('#prepareFilesDeleteComment').text("Files deleted.");
        $('#usePinLabel').text("Add a pin code");
        $('#text10-each').text("Files Links:");
        $('label[for="upload-pin"]').text("PIN code");
        $('#upload-pin').attr("placeholder", "Enter PIN code");
        $('.air-file__code-faq-text').text("Access to the unlimited download can be obtained by persons who know the PIN code. You can get the PIN code from the administration of this resource.");
        $('.air-file__code-error').text("You entered the wrong PIN code");
        $('.air-file__compression-label').text("File compression");
        $('.air-file__compression-toggle-text').text(isCompressionEnabled ? 'On' : "Off");
        if (isLoadFinishined) {
            $('#progress_text').text("UPLOADED");
        }
        $('#deletePopupDeleteBtn').val("Delete");
        $('#deletePopupCancelBtn').val("Cancel");
        $('#deletePopup h2').text("Are you sure you want to delete the downloaded files");
        $('.send_files_text').text("Send");
        $('#submitBtn').text("Send");
    }
    $('#text5').text(filesModify(fileQueue.length));
}

function filesModify(count) {
    return lang === 1 
        ? (count === 1 ? "файл" : count > 1 && count < 5 ? "файла" : "файлов")
        : (count === 1 ? "file" : "files");
}

$(document).ready(() => {
    var lang_id = getCookie("lang_id");
    if (lang_id == null) lang_id = 1;
    lang_id = parseInt(lang_id);
    if ([1, 2].includes(lang_id)) setLang(lang_id);

    let params = new URLSearchParams(document.location.search);

    $('#preloader').attr("hidden", "");
    document.getElementById('main').removeAttribute("hidden");
});