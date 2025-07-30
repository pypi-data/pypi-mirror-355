import datetime
from pydantic import ValidationError
from httpx import Client, AsyncClient
from typing import List, Optional, Union

from nanoko.models.user import Permission, User
from nanoko.models.question import Question, SubQuestion
from nanoko.exceptions import raise_nanoko_api_exception
from nanoko.models.assignment import (
    Class,
    FeedBack,
    ClassData,
    Assignment,
    TeacherClassData,
    AssignmentReviewData,
)


class UserAPI:
    """The API for the user."""

    def __init__(self, base_url: str = "http://localhost:25324", client: Client = None):
        self.base_url = base_url
        self.client = client or Client()
        self._token = None

    def register(
        self,
        username: str,
        email: str,
        display_name: str,
        password: str,
        permission: Permission,
    ) -> User:
        """Register a new user.

        Args:
            username (str): Username for the new user.
            email (str): Email address for the new user.
            display_name (str): Display name for the new user.
            password (str): Password for the new user.
            permission (Permission): Permission level for the new user.

        Returns:
            User: The created user object.
        """
        data = {
            "username": username,
            "email": email,
            "display_name": display_name,
            "password": password,
            "permission": permission.value,
        }
        response = self.client.post(f"{self.base_url}/api/v1/user/register", json=data)
        raise_nanoko_api_exception(response)
        return User.model_validate(response.json())

    def login(self, username: str, password: str) -> None:
        """Login a user.

        Args:
            username (str): Username or email of the user.
            password (str): Password of the user.

        Returns:
            None: No return value.
        """
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "username": username,
            "password": password,
        }
        response = self.client.post(
            f"{self.base_url}/api/v1/user/token", headers=headers, data=data
        )
        raise_nanoko_api_exception(response)

        self._token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self._token}"

        return None

    def me(self) -> User:
        """Get the current user's information.

        Returns:
            User: The current user's information.
        """
        response = self.client.get(f"{self.base_url}/api/v1/user/me")
        raise_nanoko_api_exception(response)
        return User.model_validate(response.json())

    def submit(self, sub_question_id: int, assignment_id: int, answer: str) -> FeedBack:
        """Submit an answer to a sub-question.

        Args:
            sub_question_id (int): The ID of the sub-question.
            assignment_id (int): The ID of the assignment.
            answer (str): The answer to the sub-question.

        Returns:
            FeedBack: The feedback on the submission.
        """
        data = {
            "sub_question_id": sub_question_id,
            "assignment_id": assignment_id,
            "answer": answer,
        }
        response = self.client.post(f"{self.base_url}/api/v1/user/submit", json=data)
        raise_nanoko_api_exception(response)
        return FeedBack.model_validate(response.json())

    def get_questions(self) -> List[Question]:
        """Get the questions created by the current user.

        Returns:
            List[Question]: The list of questions.
        """
        response = self.client.get(f"{self.base_url}/api/v1/user/questions")
        raise_nanoko_api_exception(response)
        return [Question.model_validate(q) for q in response.json()]

    def get_completed_sub_questions(
        self, assignment_id: Optional[int] = None
    ) -> List[SubQuestion]:
        """Get the completed sub-questions for the current user.

        Args:
            assignment_id (Optional[int], optional): The assignment id. Defaults to None.

        Returns:
            List[SubQuestion]: The list of completed sub-questions.
        """
        data = {}
        if assignment_id is not None:
            data["assignment_id"] = assignment_id
        response = self.client.get(
            f"{self.base_url}/api/v1/user/sub-questions/completed", params=data
        )
        raise_nanoko_api_exception(response)
        return [SubQuestion.model_validate(s) for s in response.json()]

    def get_completed_questions(self) -> List[Question]:
        """Get the completed questions for the current user.

        Returns:
            List[Question]: The list of completed questions.
        """
        response = self.client.get(f"{self.base_url}/api/v1/user/questions/completed")
        raise_nanoko_api_exception(response)
        return [Question.model_validate(q) for q in response.json()]

    def get_completed_question(self, question_id: int) -> Question:
        """Get the completed question for the current user.

        Args:
            question_id (int): The id of the question.

        Returns:
            Question: The completed question.
        """
        params = {"question_id": question_id}
        response = self.client.get(
            f"{self.base_url}/api/v1/user/question/completed", params=params
        )
        raise_nanoko_api_exception(response)
        return Question.model_validate(response.json())

    def get_assignment_image(self, assignment_id: int) -> Optional[bytes]:
        """Get the image of an assignment.

        Args:
            assignment_id (int): The id of the assignment.

        Returns:
            Optional[bytes]: The image file.
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/user/assignment/image/get",
            params={"assignment_id": assignment_id},
        )
        raise_nanoko_api_exception(response)

        if response.status_code == 204:
            return None

        return response.content

    def reset_password(self, old_password: str, new_password: str) -> dict:
        """Reset the password for the current user.

        Args:
            old_password (str): The current password of the user.
            new_password (str): The new password to set.

        Returns:
            dict: The result of the operation.
        """
        data = {"old_password": old_password, "new_password": new_password}
        response = self.client.post(
            f"{self.base_url}/api/v1/user/password/reset", json=data
        )
        raise_nanoko_api_exception(response)
        return response.json()

    def create_class(self, class_name: str, enter_code: str) -> Class:
        """Create a new class.

        Args:
            class_name (str): The name of the class.
            enter_code (str): The code to enter the class.

        Returns:
            Class: The created class object.
        """
        data = {"class_name": class_name, "enter_code": enter_code}
        response = self.client.post(
            f"{self.base_url}/api/v1/user/class/create", json=data
        )
        raise_nanoko_api_exception(response)
        return Class.model_validate(response.json())

    def join_class(self, class_name: str, enter_code: str) -> Class:
        """Join a class.

        Args:
            class_name (str): The name of the class.
            enter_code (str): The code to enter the class.

        Returns:
            Class: The joined class object.
        """
        data = {"class_name": class_name, "enter_code": enter_code}
        response = self.client.post(
            f"{self.base_url}/api/v1/user/class/join", json=data
        )
        raise_nanoko_api_exception(response)
        return Class.model_validate(response.json())

    def kick_student(self, student_id: int) -> dict:
        """Kick a student from the current class.

        Args:
            student_id (int): The id of the student to kick.

        Returns:
            dict: The result of the operation.
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/user/class/kick", json={"student_id": student_id}
        )
        raise_nanoko_api_exception(response)
        return response.json()

    def create_assignment(
        self,
        assignment_name: str,
        description: str,
        question_ids: List[int],
    ) -> Assignment:
        """Create a new assignment.

        Args:
            assignment_name (str): The name of the assignment.
            description (str): The description of the assignment.
            question_ids (List[int]): The list of question ids to include in the assignment.

        Returns:
            Assignment: The created assignment object.
        """
        data = {
            "assignment_name": assignment_name,
            "description": description,
            "question_ids": question_ids,
        }
        response = self.client.post(
            f"{self.base_url}/api/v1/user/assignment/create", json=data
        )
        raise_nanoko_api_exception(response)
        return Assignment.model_validate(response.json())

    def assign_assignment(
        self, assignment_id: int, class_id: int, due_date: datetime.datetime
    ) -> dict:
        """Assign an assignment to a class.

        Args:
            assignment_id (int): The id of the assignment.
            class_id (int): The id of the class.
            due_date (datetime.datetime): The due date of the assignment.

        Returns:
            dict: The result of the operation.
        """
        data = {
            "assignment_id": assignment_id,
            "class_id": class_id,
            "due_date": due_date.isoformat(),
        }
        response = self.client.post(
            f"{self.base_url}/api/v1/user/assignment/assign", json=data
        )
        raise_nanoko_api_exception(response)
        return response.json()

    def get_assignments(self) -> List[Assignment]:
        """Get all assignments for the current user.

        Returns:
            List[Assignment]: The list of assignments.
        """
        response = self.client.get(f"{self.base_url}/api/v1/user/assignments")
        raise_nanoko_api_exception(response)
        return [Assignment.model_validate(a) for a in response.json()]

    def get_assignment_review_data(
        self, assignment_id: int, class_id: int
    ) -> AssignmentReviewData:
        """Get the assignment review data for the current user.

        Args:
            assignment_id (int): The id of the assignment.
            class_id (int): The id of the class.

        Returns:
            AssignmentReviewData: The assignment review data.
        """
        params = {"assignment_id": assignment_id, "class_id": class_id}
        response = self.client.get(
            f"{self.base_url}/api/v1/user/assignment/review", params=params
        )
        raise_nanoko_api_exception(response)
        return AssignmentReviewData.model_validate(response.json())

    def get_class_data(
        self, class_id: Optional[int] = None
    ) -> Union[ClassData, TeacherClassData]:
        """Get the class data for the current user.
        If the user is a teacher, the class data will be returned as a TeacherClassData object.
        If the user is a student, the class data will be returned as a ClassData object.

        Args:
            class_id (Optional[int], optional): The id of the class. Defaults to None.

        Returns:
            ClassData: The class data object.
        """
        params = {}
        if class_id is not None:
            params["class_id"] = class_id
        response = self.client.get(
            f"{self.base_url}/api/v1/user/class/data", params=params
        )
        raise_nanoko_api_exception(response)
        try:
            return ClassData.model_validate(response.json())
        except ValidationError:
            return TeacherClassData.model_validate(response.json())


class AsyncUserAPI:
    """The async API for the user."""

    def __init__(
        self, base_url: str = "http://localhost:25324", client: AsyncClient = None
    ):
        self.base_url = base_url
        self.client = client or AsyncClient()
        self._token = None

    async def register(
        self,
        username: str,
        email: str,
        display_name: str,
        password: str,
        permission: Permission,
    ) -> User:
        """Register a new user.

        Args:
            username (str): Username for the new user.
            email (str): Email address for the new user.
            display_name (str): Display name for the new user.
            password (str): Password for the new user.
            permission (Permission): Permission level for the new user.

        Returns:
            User: The created user object.
        """
        data = {
            "username": username,
            "email": email,
            "display_name": display_name,
            "password": password,
            "permission": permission.value,
        }
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/register", json=data
        )
        raise_nanoko_api_exception(response)
        return User.model_validate(response.json())

    async def login(self, username: str, password: str) -> None:
        """Login a user.

        Args:
            username (str): Username or email of the user.
            password (str): Password of the user.

        Returns:
            None: No return value.
        """
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "username": username,
            "password": password,
        }
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/token", headers=headers, data=data
        )
        raise_nanoko_api_exception(response)

        self._token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self._token}"

        return None

    async def me(self) -> User:
        """Get the current user's information.

        Returns:
            User: The current user's information.
        """
        response = await self.client.get(f"{self.base_url}/api/v1/user/me")
        raise_nanoko_api_exception(response)
        return User.model_validate(response.json())

    async def submit(
        self, sub_question_id: int, assignment_id: int, answer: str
    ) -> FeedBack:
        """Submit an answer to a sub-question.

        Args:
            sub_question_id (int): The ID of the sub-question.
            assignment_id (int): The ID of the assignment.
            answer (str): The answer to the sub-question.

        Returns:
            FeedBack: The feedback on the submission.
        """
        data = {
            "sub_question_id": sub_question_id,
            "assignment_id": assignment_id,
            "answer": answer,
        }
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/submit", json=data
        )
        raise_nanoko_api_exception(response)
        return FeedBack.model_validate(response.json())

    async def get_questions(self) -> List[Question]:
        """Get the questions created by the current user.

        Returns:
            List[Question]: The list of questions.
        """
        response = await self.client.get(f"{self.base_url}/api/v1/user/questions")
        raise_nanoko_api_exception(response)
        return [Question.model_validate(q) for q in response.json()]

    async def get_completed_sub_questions(
        self, assignment_id: Optional[int] = None
    ) -> List[SubQuestion]:
        """Get the completed sub-questions for the current user.

        Args:
            assignment_id (Optional[int], optional): The assignment id. Defaults to None.

        Returns:
            List[SubQuestion]: The list of completed sub-questions.
        """
        data = {}
        if assignment_id is not None:
            data["assignment_id"] = assignment_id
        response = await self.client.get(
            f"{self.base_url}/api/v1/user/sub-questions/completed", params=data
        )
        raise_nanoko_api_exception(response)
        return [SubQuestion.model_validate(s) for s in response.json()]

    async def get_completed_questions(self) -> List[Question]:
        """Get the completed questions for the current user.

        Returns:
            List[Question]: The list of completed questions.
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/user/question/completed"
        )
        raise_nanoko_api_exception(response)
        return [Question.model_validate(q) for q in response.json()]

    async def get_completed_question(self, question_id: int) -> Question:
        """Get the completed question for the current user.

        Args:
            question_id (int): The id of the question.

        Returns:
            Question: The completed question.
        """
        params = {"question_id": question_id}
        response = await self.client.get(
            f"{self.base_url}/api/v1/user/questions/completed", params=params
        )
        raise_nanoko_api_exception(response)
        return Question.model_validate(response.json())

    async def get_assignment_image(self, assignment_id: int) -> Optional[bytes]:
        """Get the image of an assignment.

        Args:
            assignment_id (int): The id of the assignment.

        Returns:
            Optional[bytes]: The image file.
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/user/assignment/image/get",
            params={"assignment_id": assignment_id},
        )
        raise_nanoko_api_exception(response)

        if response.status_code == 204:
            return None

        return response.content

    async def reset_password(self, old_password: str, new_password: str) -> dict:
        """Reset the password for the current user.

        Args:
            old_password (str): The current password of the user.
            new_password (str): The new password to set.

        Returns:
            dict: The result of the operation.
        """
        data = {"old_password": old_password, "new_password": new_password}
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/password/reset", json=data
        )
        raise_nanoko_api_exception(response)
        return response.json()

    async def create_class(self, class_name: str, enter_code: str) -> Class:
        """Create a new class.

        Args:
            class_name (str): The name of the class.
            enter_code (str): The code to enter the class.

        Returns:
            Class: The created class object.
        """
        data = {"class_name": class_name, "enter_code": enter_code}
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/class/create", json=data
        )
        raise_nanoko_api_exception(response)
        return Class.model_validate(response.json())

    async def join_class(self, class_name: str, enter_code: str) -> Class:
        """Join a class.

        Args:
            class_name (str): The name of the class.
            enter_code (str): The code to enter the class.

        Returns:
            Class: The joined class object.
        """
        data = {"class_name": class_name, "enter_code": enter_code}
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/class/join", json=data
        )
        raise_nanoko_api_exception(response)
        return Class.model_validate(response.json())

    async def kick_student(self, student_id: int) -> dict:
        """Kick a student from the current class.

        Args:
            student_id (int): The id of the student to kick.

        Returns:
            dict: The result of the operation.
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/class/kick", json={"student_id": student_id}
        )
        raise_nanoko_api_exception(response)
        return response.json()

    async def create_assignment(
        self,
        assignment_name: str,
        description: str,
        question_ids: List[int],
    ) -> Assignment:
        """Create a new assignment.

        Args:
            assignment_name (str): The name of the assignment.
            description (str): The description of the assignment.
            question_ids (List[int]): The list of question ids to include in the assignment.

        Returns:
            Assignment: The created assignment object.
        """
        data = {
            "assignment_name": assignment_name,
            "description": description,
            "question_ids": question_ids,
        }
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/assignment/create", json=data
        )
        raise_nanoko_api_exception(response)
        return Assignment.model_validate(response.json())

    async def assign_assignment(
        self, assignment_id: int, class_id: int, due_date: datetime.datetime
    ) -> dict:
        """Assign an assignment to a class.

        Args:
            assignment_id (int): The id of the assignment.
            class_id (int): The id of the class.
            due_date (datetime.datetime): The due date of the assignment.

        Returns:
            dict: The result of the operation.
        """
        data = {
            "assignment_id": assignment_id,
            "class_id": class_id,
            "due_date": due_date.isoformat(),
        }
        response = await self.client.post(
            f"{self.base_url}/api/v1/user/assignment/assign", json=data
        )
        raise_nanoko_api_exception(response)
        return response.json()

    async def get_assignments(self) -> List[Assignment]:
        """Get all assignments for the current user.

        Returns:
            List[Assignment]: The list of assignments.
        """
        response = await self.client.get(f"{self.base_url}/api/v1/user/assignments")
        raise_nanoko_api_exception(response)
        return [Assignment.model_validate(a) for a in response.json()]

    async def get_assignment_review_data(
        self, assignment_id: int, class_id: int
    ) -> AssignmentReviewData:
        """Get the assignment review data for the current user.

        Args:
            assignment_id (int): The id of the assignment.
            class_id (int): The id of the class.

        Returns:
            AssignmentReviewData: The assignment review data.
        """
        params = {"assignment_id": assignment_id, "class_id": class_id}
        response = await self.client.get(
            f"{self.base_url}/api/v1/user/assignment/review", params=params
        )
        raise_nanoko_api_exception(response)
        return AssignmentReviewData.model_validate(response.json())

    async def get_class_data(
        self, class_id: Optional[int] = None
    ) -> Union[ClassData, TeacherClassData]:
        """Get the class data for the current user.
        If the user is a teacher, the class data will be returned as a TeacherClassData object.
        If the user is a student, the class data will be returned as a ClassData object.

        Args:
            class_id (Optional[int], optional): The id of the class. Defaults to None.

        Returns:
            ClassData: The class data object.
        """
        params = {}
        if class_id is not None:
            params["class_id"] = class_id
        response = await self.client.get(
            f"{self.base_url}/api/v1/user/class/data", params=params
        )
        raise_nanoko_api_exception(response)
        try:
            return ClassData.model_validate(response.json())
        except ValidationError:
            return TeacherClassData.model_validate(response.json())
