package dev.juanchi.jvmstartup.api;

import org.springframework.http.HttpStatus;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;
import java.util.List;

@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    ErrorResponse validationError(MethodArgumentNotValidException exception) {
        List<FieldViolation> errors = exception.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(ApiExceptionHandler::toViolation)
                .toList();
        return new ErrorResponse("validation_failed", Instant.now(), errors);
    }

    private static FieldViolation toViolation(FieldError error) {
        return new FieldViolation(error.getField(), error.getDefaultMessage());
    }

    record ErrorResponse(String code, Instant timestamp, List<FieldViolation> errors) {
    }

    record FieldViolation(String field, String message) {
    }
}
