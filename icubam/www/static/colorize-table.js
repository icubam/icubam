(function($) {

    $.fn.colorize = function(oOptions) {
        var settings = $.extend({
            parse: function(e) {
                return parseFloat(e.html());
            },
            min: undefined,
            max: undefined,
            readable: true,
            themes: {
                "default": {
                    color_min: "#C80000",
                    color_mid: "#FFFFFF",
                    color_max: "#10A54A"
                },
                "blue-white-red": {
                    color_min: "#312F9D",
                    color_mid: "#FFFFFF",
                    color_max: "#C80000"
                }
            },
            theme: "default",
            center: undefined,
            percent: false
        }, oOptions);

        var min = 0;
        var max = 0;
        this.each(function() {
            var value = parseFloat(settings.parse($(this)));
            if (!isNaN(value) && isFinite(value)) {
                min = Math.min(min, value);
                max = Math.max(max, value);
                $(this).data('colorize', value);
            }
        });

        if (settings.center === undefined) settings.center = mean(this);
        var adj = settings.center - min;

        this.each(function() {
            var value = $(this).data('colorize');
            var ratio = (settings.center - value) / adj;
            var color1, color2;

            if (!settings.percent && value <= settings.min) {
                color1 = settings.themes[settings.theme].color_min;
                color2 = settings.themes[settings.theme].color_min;
            } else if (!settings.percent && value >= settings.max) {
                color1 = settings.themes[settings.theme].color_max;
                color2 = settings.themes[settings.theme].color_max;
            } else if (settings.percent && ratio <= settings.min) {
                color1 = settings.themes[settings.theme].color_min;
                color2 = settings.themes[settings.theme].color_min;
            } else if (settings.percent && ratio >= settings.max) {
                color1 = settings.themes[settings.theme].color_max;
                color2 = settings.themes[settings.theme].color_max;
            } else if (value < settings.center) {
                ratio = Math.abs(ratio);
                if (ratio < -1) ratio = -1;
                color1 = settings.themes[settings.theme].color_min;
                color2 = settings.themes[settings.theme].color_mid;
            } else {
                ratio = Math.abs(ratio);
                if (ratio > 1) ratio = 1;
                color1 = settings.themes[settings.theme].color_max;
                color2 = settings.themes[settings.theme].color_mid;
            }
            var color = getColor(color1, color2, ratio);
            $(this).css('background-color', color);
            if (settings.readable)
                $(this).css('color', getContrastYIQ(color));
        });

        function getColor(color1, color2, ratio) {
            var hex = function(x) {
                x = x.toString(16);
                return (x.length == 1) ? '0' + x : x;
            }
            color1 = (color1.charAt(0) == "#") ? color1.slice(1) : color1
            color2 = (color2.charAt(0) == "#") ? color2.slice(1) : color2
            var r = Math.ceil(parseInt(color1.substring(0,2), 16) * ratio + parseInt(color2.substring(0,2), 16) * (1-ratio));
            var g = Math.ceil(parseInt(color1.substring(2,4), 16) * ratio + parseInt(color2.substring(2,4), 16) * (1-ratio));
            var b = Math.ceil(parseInt(color1.substring(4,6), 16) * ratio + parseInt(color2.substring(4,6), 16) * (1-ratio));
            return "#" + (hex(r) + hex(g) + hex(b)).toUpperCase();
        }

        function mean(arr) {
            var avg = 0;
            arr.each(function() {
                if ($(this).data('colorize') !== undefined) {
                    avg += $(this).data('colorize');
                }
            });
            return avg / arr.length;
        }

        // http://24ways.org/2010/calculating-color-contrast/
        function getContrastYIQ(hexcolor) {
            var hex = (hexcolor.charAt(0) == "#") ? hexcolor.slice(1) : hexcolor;
            var r = parseInt(hex.substr(0,2),16);
            var g = parseInt(hex.substr(2,2),16);
            var b = parseInt(hex.substr(4,2),16);
            var yiq = ((r*299)+(g*587)+(b*114))/1000;
            return (yiq >= 128) ? 'black' : 'white';
        }

        return this;
    };

  }(jQuery));