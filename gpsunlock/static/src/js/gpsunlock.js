 $(document).ready(function(){
     setInterval(function(){ 
         if($('img[name=coordinate_image]').length != 0 && $('img[name=coordinate_url]').length != 0){
             $('img[name=coordinate_image]').attr('src',$('input[name=coordinate_url]').val());
             $('input[name=coordinate_url]').hide();
         }
      }, 1000);
 });