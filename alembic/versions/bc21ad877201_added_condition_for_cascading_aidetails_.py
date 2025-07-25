"""Added condition for cascading aidetails if book is deleted

Revision ID: bc21ad877201
Revises: eb213b60896e
Create Date: 2025-07-22 03:55:07.773034

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bc21ad877201'
down_revision: Union[str, Sequence[str], None] = 'eb213b60896e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('book_ai_details_book_id_fkey'), 'book_ai_details', type_='foreignkey')
    op.create_foreign_key(None, 'book_ai_details', 'books', ['book_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'book_ai_details', type_='foreignkey')
    op.create_foreign_key(op.f('book_ai_details_book_id_fkey'), 'book_ai_details',
                          'books', ['book_id'], ['id'])
    # ### end Alembic commands ###
