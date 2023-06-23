function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16) / 255,
        g: parseInt(result[2], 16) / 255,
        b: parseInt(result[3], 16) / 255
    } : null;
}

function rgbToHex(rgb) {
    rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    function hex(x) {
        return ("0" + parseInt(x).toString(16)).slice(-2);
    }
    return "#" + hex(rgb[1]) + hex(rgb[2]) + hex(rgb[3]);
}


function isoCountryCodeToFlagEmoji(country) {
    if (['None', 'out-of-queries'].includes(country)) {
        return ''
    }
    return String.fromCodePoint(...[...country.toUpperCase()].map(c => c.charCodeAt() + 0x1F1A5));
}

function setColor(hex) {
    var r = document.querySelector(':root');
    r.style.setProperty('--accent-color', hex);
}

function setupClickToggle(i, j, dest, mac, cmd) {
    $(function () {
        $(`#${i}_${j}_hide_${cmd}`).click(function () {
            $(`#${i}_${j}_${cmd}`).toggleClass('strike');
            if ($(`#${i}_${j}_${cmd}`).hasClass('strike')) {
                $.post(`/dest-ctrl_${mac}_${dest}_block`)
            }
            else {
                $.post(`/dest-ctrl_${mac}_${dest}_allow`)
            }
        })
    });
}

function kFormatter(num) {
    return Math.abs(num) > 999 ? Math.sign(num)*((Math.abs(num)/1000).toFixed(1)) + 'k' : Math.sign(num)*Math.abs(num)
}