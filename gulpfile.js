var gulp = require('gulp'),
    bower = require('gulp-bower'),
    concat = require('gulp-concat-util'),
    ngAnnotate = require('gulp-ng-annotate'),
    templateCache = require('gulp-angular-templatecache'),
    addStream = require('add-stream'),
    runSequence = require('run-sequence'),
    uglify = require('gulp-uglify'),
    sourcemaps = require('gulp-sourcemaps');


var config = {
    bowerDir: './website/static/bower_components',
    vendorDir: './website/static/vendor',
    fontDir: './website/static/fonts',
    jsDir: './website/static/js',
    tplDir: './website/static/templates/**/**.html'
};

gulp.task('bower', function () {
    return bower()
        .pipe(gulp.dest(config.bowerDir));
});

gulp.task('icons', function () {
    gulp.src([
        config.bowerDir + '/bootstrap-sass/assets/fonts/bootstrap/**.*'
    ]).pipe(gulp.dest(config.fontDir + '/bootstrap'));
    gulp.src([
        config.bowerDir + '/font-awesome/fonts/**.*'
    ]).pipe(gulp.dest(config.fontDir + '/font-awesome'));
});

function prepareTemplates() {
    return gulp.src(config.tplDir + '/*.html')
        .pipe(templateCache({
            module: 'doiqApp.templates',
            transformUrl: function (url) {
                return url.replace(/\.tpl$/, '.html')
            }
        }));
}

gulp.task('angularjs', function () {
    return gulp.src([
            config.jsDir + '/app/**.js',
            config.jsDir + '/app/**/*.js'
        ])
        .pipe(addStream.obj(prepareTemplates()))
        .pipe(sourcemaps.init({loadMaps: true, identityMap: true}))
        .pipe(concat('doiqapp.js'))
        .pipe(concat.header('"use strict";\n(function() {\n'))
        .pipe(concat.footer('\n})();'))
        .pipe(ngAnnotate())
        // .pipe(uglify())
        .pipe(sourcemaps.write())
        .pipe(gulp.dest(config.jsDir + '/build/'));
});

gulp.task('templates', function () {
    return gulp.src(config.tplDir)
        .pipe(templateCache({
            module: 'DoIqApp.templates',
            templateHeader: 'angular.module("<%= module %>", []).run(["$templateCache", function($templateCache) {',
            transformUrl: function (url) {
                return '/static/templates/' + url;
            }
        }))
        .pipe(gulp.dest('./website/static/js/app'));
});

// concatenate and minify vendor sources
gulp.task('vendor', function () {
    var vendorFiles = require('./vendor.json');
    return gulp.src(vendorFiles.app)
        .pipe(sourcemaps.init({loadMaps: true, identityMap: true}))
        .pipe(concat('doiqapp-vendor.js'))
        .pipe(uglify())
        .pipe(sourcemaps.write())
        .pipe(gulp.dest(config.jsDir + '/build/'));
});

gulp.task('watch', function () {
    gulp.watch([
        config.jsDir + '/app/**.js',
        config.jsDir + '/app/**/*.js',
        config.tplDir
    ], ['angularjs', 'templates']);
});

gulp.task('default', function (done) {
    runSequence(
        'bower'
        , 'icons'
        , 'templates'
        , 'angularjs'
        , 'vendor'
        , done)
});
