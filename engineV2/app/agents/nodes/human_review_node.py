"""
Human Review Node - Implements Human-in-the-Loop (HITL) checkpoint.
Applies: Observer Pattern, State Machine
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import threading
import queue
import time

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review status states."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ReviewAction(Enum):
    """Available review actions."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    CANCEL = "cancel"


@dataclass
class ReviewRequest:
    """Data structure for review requests."""
    request_id: str
    platform: str
    extracted_data: Dict[str, Any]
    validation_result: Dict[str, Any]
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    reviewer_feedback: Optional[str] = None
    review_action: Optional[ReviewAction] = None
    timeout_seconds: int = 300  # 5 minutes default


@dataclass
class ReviewResponse:
    """Data structure for review responses."""
    request_id: str
    action: ReviewAction
    feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ReviewQueue:
    """
    Thread-safe review queue implementation.
    
    DSA: Queue (FIFO), Hash Map for fast lookup
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._queue = queue.Queue()  # Thread-safe queue
        self._active_reviews = {}  # Hash map for O(1) lookup
        self._lock = threading.Lock()
    
    def enqueue(self, review_request: ReviewRequest) -> bool:
        """
        Add review request to queue.
        
        Time Complexity: O(1)
        
        Args:
            review_request: Review request to enqueue
            
        Returns:
            Success status
        """
        try:
            with self._lock:
                self._queue.put(review_request)
                self._active_reviews[review_request.request_id] = review_request
                
            self.logger.info(
                f"Review request {review_request.request_id} enqueued"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enqueue review: {e}")
            return False
    
    def dequeue(self, timeout: Optional[int] = None) -> Optional[ReviewRequest]:
        """
        Get next review request from queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            ReviewRequest or None if timeout
        """
        try:
            review_request = self._queue.get(timeout=timeout)
            return review_request
            
        except queue.Empty:
            return None
        except Exception as e:
            self.logger.error(f"Failed to dequeue review: {e}")
            return None
    
    def get_by_id(self, request_id: str) -> Optional[ReviewRequest]:
        """
        Get review request by ID (O(1) lookup).
        
        Args:
            request_id: Request identifier
            
        Returns:
            ReviewRequest or None
        """
        with self._lock:
            return self._active_reviews.get(request_id)
    
    def update_status(
        self,
        request_id: str,
        status: ReviewStatus
    ) -> bool:
        """
        Update review request status.
        
        Args:
            request_id: Request identifier
            status: New status
            
        Returns:
            Success status
        """
        try:
            with self._lock:
                if request_id in self._active_reviews:
                    self._active_reviews[request_id].status = status
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
            return False
    
    def remove(self, request_id: str) -> bool:
        """Remove completed review request."""
        try:
            with self._lock:
                if request_id in self._active_reviews:
                    del self._active_reviews[request_id]
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove review: {e}")
            return False
    
    def get_pending_count(self) -> int:
        """Get count of pending reviews."""
        with self._lock:
            return sum(
                1 for review in self._active_reviews.values()
                if review.status == ReviewStatus.PENDING
            )


class ReviewObserver:
    """
    Observer for review status changes.
    
    Design Pattern: Observer Pattern
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._observers: List[Callable] = []
    
    def subscribe(self, callback: Callable) -> None:
        """Subscribe to review events."""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from review events."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def notify(self, event_data: Dict[str, Any]) -> None:
        """Notify all observers of review event."""
        for callback in self._observers:
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(f"Observer notification failed: {e}")


class HumanReviewNode:
    """
    Main Human Review Node with state management.
    
    Design Pattern: State Pattern, Observer Pattern
    OOP: Composition, Encapsulation
    DSA: Queue, Hash Map
    """
    
    def __init__(self, timeout_seconds: int = 300):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timeout_seconds = timeout_seconds
        self.review_queue = ReviewQueue()
        self.observer = ReviewObserver()
        self._timeout_monitor_thread = None
        self._monitor_active = False
        self._start_timeout_monitor()
    
    def _start_timeout_monitor(self) -> None:
        """Start background thread to monitor timeouts."""
        try:
            self._monitor_active = True
            self._timeout_monitor_thread = threading.Thread(
                target=self._monitor_timeouts,
                daemon=True
            )
            self._timeout_monitor_thread.start()
            self.logger.info("Timeout monitor started")
            
        except Exception as e:
            self.logger.error(f"Failed to start timeout monitor: {e}")
    
    def _monitor_timeouts(self) -> None:
        """Monitor review requests for timeouts."""
        while self._monitor_active:
            try:
                current_time = datetime.now()
                
                # Check all active reviews
                for request_id, review in list(
                    self.review_queue._active_reviews.items()
                ):
                    if review.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
                        elapsed = (current_time - review.created_at).total_seconds()
                        
                        if elapsed > review.timeout_seconds:
                            self.logger.warning(
                                f"Review {request_id} timed out after {elapsed}s"
                            )
                            
                            # Update status to timeout
                            self.review_queue.update_status(
                                request_id,
                                ReviewStatus.TIMEOUT
                            )
                            
                            # Notify observers
                            self.observer.notify({
                                'event': 'timeout',
                                'request_id': request_id,
                                'timestamp': current_time
                            })
                
                # Sleep for 1 second before next check
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Timeout monitor error: {e}")
    
    def request_review(
        self,
        platform: str,
        extracted_data: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a review request.
        
        Args:
            platform: Platform identifier
            extracted_data: Extracted data
            validation_result: Validation result
            
        Returns:
            Review request information
        """
        try:
            # Generate unique request ID
            request_id = f"review_{platform}_{int(time.time() * 1000)}"
            
            # Create review request
            review_request = ReviewRequest(
                request_id=request_id,
                platform=platform,
                extracted_data=extracted_data,
                validation_result=validation_result,
                timeout_seconds=self.timeout_seconds
            )
            
            # Enqueue request
            success = self.review_queue.enqueue(review_request)
            
            if not success:
                raise RuntimeError("Failed to enqueue review request")
            
            self.logger.info(f"Review requested: {request_id}")
            
            # Notify observers
            self.observer.notify({
                'event': 'review_requested',
                'request_id': request_id,
                'platform': platform
            })
            
            return {
                'success': True,
                'request_id': request_id,
                'status': ReviewStatus.PENDING.value,
                'message': 'Review request created successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to request review: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_review(
        self,
        request_id: str,
        action: ReviewAction,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit human review decision.
        
        Args:
            request_id: Review request identifier
            action: Review action
            feedback: Optional feedback text
            
        Returns:
            Review submission result
        """
        try:
            # Get review request
            review_request = self.review_queue.get_by_id(request_id)
            
            if not review_request:
                raise ValueError(f"Review request {request_id} not found")
            
            if review_request.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
                raise ValueError(f"Review {request_id} already completed")
            
            # Update review request
            review_request.status = (
                ReviewStatus.APPROVED if action == ReviewAction.APPROVE
                else ReviewStatus.REJECTED
            )
            review_request.reviewed_at = datetime.now()
            review_request.reviewer_feedback = feedback
            review_request.review_action = action
            
            # Update in queue
            self.review_queue.update_status(request_id, review_request.status)
            
            self.logger.info(
                f"Review {request_id} {action.value} by human"
            )
            
            # Notify observers
            self.observer.notify({
                'event': 'review_completed',
                'request_id': request_id,
                'action': action.value,
                'feedback': feedback
            })
            
            return {
                'success': True,
                'request_id': request_id,
                'action': action.value,
                'status': review_request.status.value,
                'message': 'Review submitted successfully'
            }
            
        except ValueError as e:
            self.logger.error(f"Review submission error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Failed to submit review: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Review submission error: {str(e)}"
            }
    
    def get_review_status(self, request_id: str) -> Dict[str, Any]:
        """
        Get current status of review request.
        
        Args:
            request_id: Review request identifier
            
        Returns:
            Review status information
        """
        try:
            review_request = self.review_queue.get_by_id(request_id)
            
            if not review_request:
                return {
                    'success': False,
                    'error': 'Review request not found'
                }
            
            return {
                'success': True,
                'request_id': request_id,
                'status': review_request.status.value,
                'platform': review_request.platform,
                'created_at': review_request.created_at.isoformat(),
                'reviewed_at': (
                    review_request.reviewed_at.isoformat()
                    if review_request.reviewed_at else None
                ),
                'feedback': review_request.reviewer_feedback
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get review status: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """Get all pending review requests."""
        try:
            pending_reviews = []
            
            for request_id, review in self.review_queue._active_reviews.items():
                if review.status == ReviewStatus.PENDING:
                    pending_reviews.append({
                        'request_id': request_id,
                        'platform': review.platform,
                        'created_at': review.created_at.isoformat(),
                        'validation_issues': review.validation_result.get('total_issues', 0)
                    })
            
            return pending_reviews
            
        except Exception as e:
            self.logger.error(f"Failed to get pending reviews: {e}")
            return []
    
    def cleanup_completed_reviews(self, older_than_hours: int = 24) -> int:
        """
        Clean up old completed reviews.
        
        Args:
            older_than_hours: Remove reviews older than this
            
        Returns:
            Number of reviews removed
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            removed_count = 0
            
            for request_id, review in list(
                self.review_queue._active_reviews.items()
            ):
                if review.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
                    if review.reviewed_at and review.reviewed_at < cutoff_time:
                        self.review_queue.remove(request_id)
                        removed_count += 1
            
            self.logger.info(f"Cleaned up {removed_count} old reviews")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return 0
