#pragma once

// https://www.programiz.com/dsa/circular-queue


struct EventQueue
{
    SDL_Event* buf;
    int front;
    int rear;
    int size;
};

void queue_init(struct EventQueue* q, int size)
{
    q->buf = (SDL_Event*)malloc(size * sizeof(SDL_Event));
    q->front = -1;
    q->rear = -1;
    q->size = size;
}

bool queue_full(struct EventQueue* q) {
    if ((q->front == q->rear + 1) || (q->front == 0 && q->rear == q->size - 1)) 
        return true;
    return false;
}

bool queue_empty(struct EventQueue* q) {
  if (q->front == -1)
      return true;
  return false;
}

SDL_Event* queue_enq(struct EventQueue* q) {
    if (queue_full(q)) {
        printf("\n Queue is full!! \n");
        return NULL;
    }
    if (q->front == -1) 
        q->front = 0;
    q->rear = (q->rear + 1) % q->size;
    return &q->buf[q->rear];
}

SDL_Event* queue_deq(struct EventQueue* q) 
{
    if (queue_empty(q)) {
        return NULL;
    }
    SDL_Event* element = &q->buf[q->front];
    if (q->front == q->rear) {
        q->front = -1;
        q->rear = -1;
    } 
    else {
        q->front = (q->front + 1) % q->size;
    }
    return element;
}