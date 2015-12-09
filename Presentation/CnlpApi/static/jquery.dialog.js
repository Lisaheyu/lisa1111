(function ($){
    var options = {};
 
    $.fn.act_as_dialog = function (width, height, borderwidth, bordercolor, autoscroll)
    {
        var style = 'display:block;overflow-x: no;overflow-y: auto;word-break:break-all;border:' + borderwidth + 'px solid ' + bordercolor + '; width:' + width + 'px;height:' + height + 'px;';
        this.attr('style', style);
 
        options['autoscroll'] = autoscroll;
    }
    $.fn.append_line = function (user, time, line)
    {
        this.append('<p>' + user + ' ' + time + '<br/>' + line + '</p>');
        if (options['autoscroll'] == 'yes')
            this.scrollTop(this.attr('scrollHeight') - this.height());
    }
    $.fn.set_auto_scroll = function(autoscroll)
    {
        options['autoscroll'] = autoscroll;
    }
})(jQuery);
 
(function ($){
    $.fn.act_as_input = function(width, callback)
    {
        var style = 'width:' + width + 'px;';
        this.attr('style', style);
 
        var _This = this;
        this.bind('keydown', function saysth(e)
        { 
            var sth = _This.val();
            if (e.which == 13)
            {
                if (sth != '')
                {
                    callback(sth);
                    _This.val('');
                }
            }
        });
    }
})(jQuery);