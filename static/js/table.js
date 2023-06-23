const h = $('.scroll').height();
const max = $('.scroll').css("max-height");
if (h < parseInt(max)) {
    $('.fadeout').css('background-image', 'none');
}