module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    uglify: {
      options: {
        mangle: false
      },
      build: {
        src: ['src/static/app/app.js', 'src/static/app/services/*.js', 'src/static/app/directives/*.js', 'src/static/app/controllers/*.js'],
        dest: 'src/static/app/app.min.js'
      },
    },
    watch: {
      less: {
        files: ['src/static/less/*.less'],
        tasks: ['less']
      },
      app: {
        files: ['src/static/app/app.js', 'src/static/app/directives/*.js', 'src/static/app/controllers/*.js'],
        tasks: ['uglify']
      }
    },
    less: {
      development: {
        options: {
          compress: true,
          yuicompress: true,
          optimization: 2
        },
        files: {
          'src/static/css/styles.min.css': 'src/static/less/*.less'
        }
      }
    },
  });

  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-jshint');

  grunt.registerTask('default', ['uglify', 'less', 'watch']);

};
