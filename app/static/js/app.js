$( document ).ready(function() {
 
    $('[data-toggle="tooltip"]').tooltip();

    $('.movie-item').on('click', function(e){
        e.preventDefault();
        $('.movie-item').css({'background-color':'transparent', 'color':'#5a5a5a'});
        $(this).css({'background-color':'#80CCEC', 'color':'#fff'});
        movieId = $(this).data()['movieId'];
        $('.movie').hide();
        $('#'+movieId).css('top', $(this).position().top);
        $('#'+movieId).show();
    });
 
});