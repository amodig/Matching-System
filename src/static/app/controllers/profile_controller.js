MatchingApp.controller('ProfileController', function($scope, $rootScope, Api, Fileupload){
  $rootScope.activeLink = 'profile';

  $scope.bio = {
    editing: false,
    content: '**Lorem ipsum**, dolor sit amet',
    files: []
  };

  Api.getProfile().success(function(profile){
    console.log(profile);
  });

  Fileupload.init($scope.bio.files);

  $scope.editBio = function(){
    $scope.bio.editing = true;
  }

  $scope.updateBio = function(){
    Api.updateBio($scope.bio.content).success(function(){
      $scope.bio.editing = false;
    });
  }
});
