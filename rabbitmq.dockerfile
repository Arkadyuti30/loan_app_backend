FROM rabbitmq

# Define environment variables.
ENV RABBITMQ_USER user
ENV RABBITMQ_PASSWORD user
ENV RABBITMQ_PID_FILE /var/lib/rabbitmq/mnesia/rabbitmq

EXPOSE 15672

# Define default command
CMD ["rabbitmq-plugins", "enable rabbitmq_management"]