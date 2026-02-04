"""People API v2: household profiles within a tenant."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotPerson, HomebotUser
from app.schemas.v2.people import PersonCreate, PersonResponse, PersonUpdate

router = APIRouter()


async def _ensure_user_in_tenant(user_id: UUID, db: AsyncSession) -> None:
    """Validate that the linked user exists in the active tenant."""
    result = await db.execute(select(HomebotUser).where(HomebotUser.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found in tenant",
        )


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    body: PersonCreate,
    tenant_id: UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> PersonResponse:
    """Create a household profile within the tenant."""
    if body.user_id:
        await _ensure_user_in_tenant(body.user_id, db)
    person = HomebotPerson(
        tenant_id=tenant_id,
        user_id=body.user_id,
        name=body.name,
        nickname=body.nickname,
        avatar_url=body.avatar_url,
        color=body.color,
        dietary_restrictions=body.dietary_restrictions,
        allergies=body.allergies,
        is_active=body.is_active,
    )
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return PersonResponse.model_validate(person)


@router.get("", response_model=list[PersonResponse])
async def list_people(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> list[PersonResponse]:
    """List household profiles; default excludes inactive profiles."""
    stmt = select(HomebotPerson)
    if not include_inactive:
        stmt = stmt.where(HomebotPerson.is_active.is_(True))
    stmt = stmt.order_by(HomebotPerson.name)
    result = await db.execute(stmt)
    people = result.scalars().all()
    return [PersonResponse.model_validate(person) for person in people]


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: UUID,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> PersonResponse:
    """Get a household profile by ID."""
    result = await db.execute(select(HomebotPerson).where(HomebotPerson.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return PersonResponse.model_validate(person)


@router.patch("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: UUID,
    body: PersonUpdate,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> PersonResponse:
    """Update a household profile (partial)."""
    result = await db.execute(select(HomebotPerson).where(HomebotPerson.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    data = body.model_dump(exclude_unset=True)
    if "user_id" in data and data["user_id"] is not None:
        await _ensure_user_in_tenant(data["user_id"], db)
    for key, value in data.items():
        setattr(person, key, value)
    await db.commit()
    await db.refresh(person)
    return PersonResponse.model_validate(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_person(
    person_id: UUID,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> None:
    """Deactivate a household profile (soft delete)."""
    result = await db.execute(select(HomebotPerson).where(HomebotPerson.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    if person.is_active:
        person.is_active = False
        await db.commit()
