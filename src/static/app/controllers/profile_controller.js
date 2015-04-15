MatchingApp.controller('ProfileController', function($scope, Api, Fileupload){
  $scope.bio = {
    editing: false,
    content: '**Lorem ipsum**, dolor sit amet'
  };

  Api.getProfile().success(function(profile){
    console.log(profile);
  });

  var waitForFiles = $scope.$watch('bio', function(newVal, oldVal){
    if(newVal.files){
      Fileupload.init($scope.bio.files);
      waitForFiles();
    }
  });

  $scope.editBio = function(){
    $scope.bio.editing = true;
  }

  $scope.updateBio = function(){
    Api.updateBio($scope.bio.content).success(function(){
      $scope.bio.editing = false;
    });
  }
});
