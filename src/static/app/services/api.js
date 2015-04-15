MatchingApp.service('Api', function($http){
  this.updateBio = function(newBio){
    return $http.post('/update_bio', { bio_new_text: newBio });
  }

  this.getProfile = function(){
    return $http.get('/profile');
  }
});
