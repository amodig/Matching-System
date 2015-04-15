MatchingApp.controller('ProfileController', function($scope, Api){
  $scope.bio = {
    editing: false,
    content: '**Lorem ipsum**, dolor sit amet'
  };

  $scope.editBio = function(){
    $scope.bio.editing = true;
  };

  $scope.updateBio = function(){
    Api.updateBio($scope.bio.content).success(function(){
      $scope.bio.editing = false;
    });
  }
});
